extends Node
## One life's state: age, quarter, stats, flags and the yearly super like (GDD §2–§4).

const ACTIONS_PER_YEAR := 12  # GDD §6.5: 3 per card turn from 13
const STATS := [
	"health",
	"happiness",
	"money",
	"career",
	"relationships",
	"smarts",
	"looks",
	"karma",
	"stress",
	"boldness",
	"sociability",
	"fame",
	"infamy",
]
## Fame and Infamy (GDD §15.11) start at 0; the player sees the fame tier, not the number.
const HIDDEN_STATS := ["karma", "fame", "infamy"]  # GDD §4.4
const ZERO_STATS := ["money", "stress", "fame", "infamy"]
## Fame tiers (GDD §15.11): the lowest Fame of each tier; under the first is tier 0 (nobody).
const FAME_TIERS := ["local", "rising", "known", "famous", "star", "icon"]
const FAME_TIER_AT := [5, 20, 40, 60, 80, 95]
const UNBOUNDED_STATS := ["money"]  # GDD §4.3: every other stat is 0–100
## Spectrums (GDD §4.6): 0 = Cautious / Introvert, 100 = Risk-taker / Extrovert.
const TRAITS := ["boldness", "sociability"]

var age := 0
var quarter := 0  # 0–3: which of the year's 4 cards is next (GDD §2.1)
var stats := {}
var flags := {}  # also holds illnesses (LifeRules.ILLNESSES)
var used := {}  # card ids drawn this life ("once" cards never repeat)
var super_like_available := true  # one per year (GDD §3.3)
var actions_left := ACTIONS_PER_YEAR  # between-year menu budget (GDD §6.5)
var careers := {}  # slot ("job" / "special") -> entry; see CareerRules
var partner := {}  # {} = single, else {name, affinity, met}; outlives the job it came from
var children := []  # {name, born_at (your age then), affinity, look, adopted}; see Family
var parents_alive := true
var look := {}  # Looks: chosen at the start of a life
var housing := {"kind": "parents"}  # parents / rent / own (+ house, label, value, upkeep, growth)
var debts := []  # {kind: mortgage / student / loan, balance, rate, payment, taken}; see Finance
var savings := 0
var investments := 0
var invest_bold := false
var debt_years := 0  # years in a row ending with a loan; repossession follows (Finance)
var fresh_start_until := 0
var course := {}  # the course in progress; see Finance.enrol
var loan_years := 0  # course years already put on a student loan; see Finance.loan_open
var items := []  # ids of bought shop items; see Items
var siblings := []  # {name, look}: the heir's brothers and sisters; see Legacy


func _ready() -> void:
	new_life()


func new_life() -> void:
	age = 0
	quarter = 0
	flags = {}
	used = {}
	super_like_available = true
	actions_left = actions_per_year(0)
	careers = {}
	partner = {}
	children = []
	parents_alive = true
	look = {}
	housing = {"kind": "parents"}
	debts = []
	savings = 0
	investments = 0
	invest_bold = false
	debt_years = 0
	fresh_start_until = 0
	course = {}
	loan_years = 0
	items = []
	siblings = []
	stats = {}
	for s in STATS:
		stats[s] = 0 if s in ZERO_STATS else 50
	for s in TRAITS:
		stats[s] = randi_range(40, 60)


func change_stat(stat: String, delta: int) -> void:
	var v: int = stats[stat] + delta
	stats[stat] = v if stat in UNBOUNDED_STATS else clampi(v, 0, 100)


func to_dict() -> Dictionary:
	return {
		"age": age,
		"quarter": quarter,
		"stats": stats,
		"flags": flags,
		"used": used,
		"super_like_available": super_like_available,
		"actions_left": actions_left,
		"careers": careers,
		"partner": partner,
		"children": children,
		"parents_alive": parents_alive,
		"look": look,
		"housing": housing,
		"debts": debts,
		"savings": savings,
		"investments": investments,
		"invest_bold": invest_bold,
		"debt_years": debt_years,
		"fresh_start_until": fresh_start_until,
		"course": course,
		"loan_years": loan_years,
		"items": items,
		"siblings": siblings,
	}


func from_dict(d: Dictionary) -> void:
	age = int(d.age)
	quarter = int(d.quarter)
	flags = d.flags
	used = d.get("used", {})
	super_like_available = d.super_like_available
	actions_left = int(d.get("actions_left", ACTIONS_PER_YEAR))
	careers = d.get("careers", {})
	partner = d.get("partner", {})
	children = d.get("children", [])
	parents_alive = d.get("parents_alive", true)
	look = d.get("look", {})
	housing = d.get("housing", {"kind": "parents"})
	debts = d.get("debts", [])
	savings = int(d.get("savings", 0))
	investments = int(d.get("investments", 0))
	invest_bold = d.get("invest_bold", false)
	debt_years = int(d.get("debt_years", 0))
	fresh_start_until = int(d.get("fresh_start_until", 0))
	course = d.get("course", {})
	loan_years = int(d.get("loan_years", 0))
	items = d.get("items", [])
	siblings = d.get("siblings", [])
	for entry in careers.values():  # JSON reads numbers back as floats
		for k in ["rank", "performance", "years", "meter"]:
			entry[k] = int(entry[k])
		for role in entry.coworkers:
			entry.coworkers[role].affinity = int(entry.coworkers[role].affinity)
	for child: Dictionary in children:
		child.born_at = int(child.born_at)
		child.affinity = int(child.affinity)
	if partner.has("affinity"):
		partner.affinity = int(partner.affinity)
	for s in STATS:
		var fallback: int = 0 if s in ZERO_STATS else stats.get(s, 50 if s in TRAITS else 0)
		stats[s] = int(d.stats.get(s, fallback))


## 0 (nobody) to 6 (icon): index into FAME_TIERS is tier - 1.
func fame_tier() -> int:
	return tier_of(int(stats.get("fame", 0)))


## The fame tier's name, "" for nobody.
func fame_tier_name() -> String:
	var t := fame_tier()
	return FAME_TIERS[t - 1] if t > 0 else ""


static func tier_of(fame: int) -> int:
	var t := 0
	for at in FAME_TIER_AT:
		if fame >= at:
			t += 1
	return t


## Menu actions per year by age (GDD §6.5): 1 per card turn under 6, 2 under 13, then 3.
static func actions_per_year(at_age: int) -> int:
	if at_age < 6:
		return 4
	if at_age < 13:
		return 8
	return ACTIONS_PER_YEAR
