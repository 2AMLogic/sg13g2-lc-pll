# frozen_string_literal: true
#
# Enumerate the RDB rule categories the IHP SG13G2 KLayout DRC runset
# *declares*, from the deck source alone (issue #36, T1 item 3).
#
# Why this exists
# ---------------
# `klt drc --engine klayout` grades a zero-violation native run
# `coverage_unknown`, not `clean`: KLayout's RDB records the categories a deck
# declared, but klt has no way to know whether that set is the whole deck or a
# switch-gated fragment. `klt drc --expect-rule-categories-file` lifts the run
# to `clean` when the caller vouches for the exact set -- and the klt docs are
# explicit that the list must be established *independently* of the run being
# accepted: "copying the accepted run's own categories is circular".
#
# This script is that independent establishment. It loads the deck's own Ruby
# source (including the `# %include` chain, which KLayout splices textually),
# evaluates it with every KLayout DRC primitive replaced by an inert stub, and
# records every `.output(<category>, <description>)` call the deck's own
# control flow reaches for a given switch set. No layout is read, no DRC runs,
# and klt is not involved, so the result cannot be contaminated by the report
# it is used to accept.
#
# What it can and cannot see
# --------------------------
# Category emission in this deck is almost entirely gated on the `-rd` switch
# globals (TABLES / FEOL / BEOL / PIN / FORBIDDEN / RECOMMENDED / OFFGRID /
# ANGLE / PRECHECK_DRC) and on loops over literal layer tables, all of which
# this evaluation reproduces exactly. The density and antenna rule files, whose
# rules declare a category only when a measured density is out of range, are
# not `%include`d by `ihp-sg13g2.drc` at all.
#
# Three quantities the deck reads from the layout remain, and this script makes
# each an explicit input rather than assuming it:
#
#   * `--chip-area`     -> `en_tiles` (chip area > 1e6 um2). Switches KLayout's
#                          run mode only; it guards no `output` call.
#   * `--region-area`   -> every derived region's area. The only consumer in
#                          the included set is `MIM.gR` (rule_decks/beol/
#                          6_11_mim.drc), declared only when total MIM area
#                          exceeds the recommended maximum (174800 um2).
#   * no EdgeSeal boundary -> every derived region reports `is_empty?`. The
#                          only consumer in the include chain is `Seal.l`
#                          (rule_decks/beol/6_10_sealring.drc), which the deck
#                          declares only when `edgeseal_bound` (39/4) meets the
#                          chip extent. This one is a fixed premise rather than
#                          a flag: the deck reaches `Seal.l` through a helper
#                          that reads a file path built from `__FILE__`, which
#                          textual splicing does not preserve, so the branch
#                          cannot be exercised here. The test verifies the
#                          premise directly instead -- layer 39/4 is absent
#                          from `layout/top.gds` -- and fails if it ever
#                          appears.
#
# A list is therefore valid for a deck revision, a switch set AND those
# premises. `scripts/test-native-rule-categories.sh` measures the premises
# against `layout/top.gds`, shows the derived set is sensitive to each of them,
# and re-checks that no further geometry-gated rule file has entered the
# include chain -- so a PDK bump that breaks any of it fails loudly instead of
# silently narrowing the asserted set.
#
# Usage
#   ruby native_rule_categories.rb --deck <ihp-sg13g2.drc> [--out PATH] \
#        [--provenance PATH] [--pdk-root PATH] [--chip-area UM2] \
#        [--region-area UM2] [--set NAME=VALUE ...]
#
# `--set` assigns a deck global exactly as `klt drc --deck-var NAME=VALUE`
# would (e.g. `--set tables=main`). Unset globals take the deck's own
# in-script defaults, which is what a run with no `--deck-var` gets.
#
#
# `--pdk-root` is recorded in, and strips its own prefix from, the provenance
# paths so a committed provenance file carries PDK-relative paths rather than
# this host's install location.
#
# `--provenance` writes the sha256 of every file in the `%include` chain, the
# switch set and the category count, so a committed list can be re-checked
# against the PDK revision it was derived from. `klt drc` records a content
# hash for the top-level deck file only, which does not cover the rule files
# the deck splices in.

require 'json'
require 'set'
require 'tmpdir'

# --------------------------------------------------------------------------
# argument parsing
# --------------------------------------------------------------------------
deck_path = nil
out_path = nil
provenance_path = nil
pdk_root = nil
chip_area = 0.0
region_area = 0.0
deck_vars = {}

args = ARGV.dup
until args.empty?
  arg = args.shift
  case arg
  when '--deck' then deck_path = args.shift
  when '--out' then out_path = args.shift
  when '--provenance' then provenance_path = args.shift
  when '--pdk-root' then pdk_root = args.shift
  when '--chip-area' then chip_area = args.shift.to_f
  when '--region-area' then region_area = args.shift.to_f
  when '--set'
    assignment = args.shift.to_s
    name, _, value = assignment.partition('=')
    abort("--set expects NAME=VALUE, got #{assignment.inspect}") if name.empty?
    deck_vars[name] = value
  when '--help', '-h'
    puts File.read(__FILE__).lines.grep(/^#/).join
    exit 0
  else
    abort("unknown argument #{arg.inspect}")
  end
end
abort('--deck is required') if deck_path.nil?
deck_path = File.expand_path(deck_path)
abort("no such deck: #{deck_path}") unless File.file?(deck_path)

# --------------------------------------------------------------------------
# %include splicing -- KLayout's DRC preprocessor reads `# %include <path>`
# comment lines and splices the named file in textually, relative to the
# including file's directory. Local variables therefore carry across the
# boundary, which the rule decks rely on (every rule file reads the layer
# locals defined in rule_decks/layers_def.drc).
# --------------------------------------------------------------------------
INCLUDE_RE = /\A\s*#\s*%include\s+(\S+)\s*\z/
SPLICED_FILES = []

def splice(path, seen = [])
  abort("include cycle at #{path}") if seen.include?(path)
  SPLICED_FILES << path
  dir = File.dirname(path)
  File.readlines(path, chomp: true).flat_map do |line|
    m = INCLUDE_RE.match(line)
    if m
      child = File.expand_path(m[1], dir)
      abort("included file not found: #{child}") unless File.file?(child)
      ["# >>> spliced #{child}"] + splice(child, seen + [path]) + ['# <<< end splice']
    else
      [line]
    end
  end
end

DECK_SOURCE = splice(deck_path).join("\n")

# --------------------------------------------------------------------------
# stub layer algebra
# --------------------------------------------------------------------------
$declared_categories = []
$declared_descriptions = {}

# Stands in for every DRC::Region / DRC::Edges / DRC::EdgePairs value. Every
# layer operation returns another stub, so the deck's expression trees build
# and tear down exactly as written; only `output` has an effect.
class StubLayer
  def output(category, description = nil)
    name = category.to_s
    $declared_categories << name
    $declared_descriptions[name] ||= description.to_s
    nil
  end

  # Operations whose results the deck inspects as plain values, rather than
  # chaining further layer algebra onto. Each is an explicit input -- see the
  # header note on premises.
  def count = 0
  def area = $stub_region_area
  def is_empty? = true
  def bbox = StubBox.new
  def nil? = false
  def polygons? = true
  def edges? = false
  def is_merged? = true
  def to_s = '<stub layer>'
  def inspect = '<stub layer>'

  # Block-taking selectors: the predicate is never evaluated, so no geometry
  # is invented.
  def select(*_args) = self
  def each(*_args) = self

  def method_missing(_name, *_args, &_blk) = self
  def respond_to_missing?(_name, _private = false) = true
end

class StubBox
  def width = 0.0
  def height = 0.0
  def left = 0.0
  def right = 0.0
  def top = 0.0
  def bottom = 0.0
  def method_missing(_name, *_args, &_blk) = 0.0
  def respond_to_missing?(_name, _private = false) = true
end

# KLayout's unit suffixes. The deck only ever compares these against each
# other, so the scale is irrelevant to which categories are declared; keeping
# the real scale makes any accidental dependency behave as it would in KLayout.
class Numeric
  def um = self
  def nm = self / 1000.0
  def mm = self * 1000.0
  def um2 = self
  def dbu = self / 1000.0
  def degree = self
  def percent = self
end

# RBA bits the deck's logger touches.
module RBA
  class Timer
    def self.memory_size = 0
  end

  class CellView
    def self.active = nil
  end
end

# --------------------------------------------------------------------------
# evaluation
# --------------------------------------------------------------------------
# Deck globals, assigned exactly as `klt drc --deck-var NAME=VALUE` does.
# `input` and `report` are always set by klt; `log` is the deck's logger sink.
# The chip extent is a distinguished stub: `en_tiles` reads *its* area, which
# is a different quantity from the per-layer areas rule files measure.
class StubChip < StubLayer
  def area = $stub_chip_area
end

def extent = StubChip.new

$stub_chip_area = chip_area
$stub_region_area = region_area
log_sink = File.join(Dir.tmpdir, "native-rule-categories-#{Process.pid}.log")
deck_vars.each { |name, value| eval("$#{name} = #{value.inspect}", TOPLEVEL_BINDING) }
$log ||= log_sink
$report ||= File.join(Dir.tmpdir, "native-rule-categories-#{Process.pid}.lyrdb")
# `$input` is deliberately left nil: the deck skips `source(...)` and no
# layout is ever read.

# Any bare identifier the deck uses that is not a Ruby local -- every KLayout
# DRC primitive (`polygons`, `labels`, `extent`, `euclidian`, `props_eq`,
# `connect`, `tiles`, ...) -- resolves here and yields an inert stub.
TOPLEVEL_BINDING.receiver.instance_eval do
  def method_missing(_name, *_args, &_blk) = StubLayer.new
  def respond_to_missing?(_name, _private = false) = true
end

# Silence the deck's progress logging; it writes to $stdout via Logger.
original_stdout = $stdout
$stdout = File.open(File::NULL, 'w')
begin
  eval(DECK_SOURCE, TOPLEVEL_BINDING, deck_path)
ensure
  $stdout.close
  $stdout = original_stdout
  File.unlink(log_sink) if File.exist?(log_sink)
  File.unlink($report) if $report && File.exist?($report)
end

categories = $declared_categories
unique = categories.uniq.sort

duplicates = categories.tally.select { |_, n| n > 1 }
unless duplicates.empty?
  warn("note: #{duplicates.size} category name(s) declared by more than one " \
       "output call: #{duplicates.keys.sort.join(', ')}")
end

body = unique.join("\n") + "\n"
if out_path
  File.write(out_path, body)
  warn("wrote #{unique.size} categories to #{out_path}")
else
  print body
end

if provenance_path
  require 'digest'
  root = File.dirname(deck_path)
  strip = pdk_root ? File.expand_path(pdk_root) : root
  provenance = {
    'schema_version' => 1,
    'producer' => 'layout/drc/native_rule_categories.rb',
    'deck' => deck_path.sub(/\A#{Regexp.escape(strip)}\//, ''),
    'paths_relative_to' => pdk_root ? '--pdk-root' : 'deck directory',
    'deck_vars' => deck_vars,
    'premises' => {
      'chip_area_um2' => chip_area,
      'region_area_um2' => region_area,
      'edgeseal_boundary_present' => false
    },
    'category_count' => unique.size,
    'include_chain' => SPLICED_FILES.map do |path|
      {
        'path' => path.sub(/\A#{Regexp.escape(strip)}\//, ''),
        'content_hash' => "sha256:#{Digest::SHA256.file(path).hexdigest}"
      }
    end
  }
  File.write(provenance_path, JSON.pretty_generate(provenance) + "\n")
  warn("wrote provenance for #{SPLICED_FILES.size} deck files to #{provenance_path}")
end
