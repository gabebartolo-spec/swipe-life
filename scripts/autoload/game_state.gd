extends Node
## One life's state: age, quarter, stats, flags and the yearly super like (GDD §2–§4).

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
	"sociability"
]
const HIDDEN_STATS := ["karma"]  # GDD §4.4
const UNBOUNDED_STATS := ["money"]  # GDD §4.3: every other stat is 0–100
## Spectrums (GDD §4.6): 0 = Cautious / Introvert, 100 = Risk-taker / Extrovert.
const TRAITS := ["boldness", "sociability"]

var age := 0
var quarter := 0  # 0–3: which of the year's 4 cards is next (GDD §2.1)
var stats := {}
var flags := {}  # also holds illnesses (LifeRules.ILLNESSES)
var used := {}  # card ids drawn this life ("once" cards never repeat)
var super_like_available := true  # one per year (GDD §3.3)
var careers := {}  # slot ("job" / "special") -> entry; see CareerRules
var partner := {}  # {} = single, else {name, affinity, met}; outlives the job it came from
var look := {}  # Looks: chosen at the start of a life
var housing := {"kind": "parents"}  # parents / rent / own (+ house, label, value, upkeep, growth)
var debts := []  # {kind: mortgage / student / loan, balance, rate, payment, taken}; see Finance
var savings := 0
var investments := 0
var invest_bold := false
var debt_years := 0  # years in a row ending with a loan; repossession follows (Finance)
var fresh_start_until := 0
var course := {}  # the course in progress; see Finance.enrol


func _ready() -> void:
	new_life()


func new_life() -> void:
	age = 0
	quarter = 0
	flags = {}
	used = {}
	super_like_available = true
	careers = {}
	partner = {}
	look = {}
	housing = {"kind": "parents"}
	debts = []
	savings = 0
	investments = 0
	invest_bold = false
	debt_years = 0
	fresh_start_until = 0
	course = {}
	stats = {}
	for s in STATS:
		stats[s] = 0 if s in UNBOUNDED_STATS or s == "stress" else 50
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
		"careers": careers,
		"partner": partner,
		"look": look,
		"housing": housing,
		"debts": debts,
		"savings": savings,
		"investments": investments,
		"invest_bold": invest_bold,
		"debt_years": debt_years,
		"fresh_start_until": fresh_start_until,
		"course": course,
	}


func from_dict(d: Dictionary) -> void:
	age = int(d.age)
	quarter = int(d.quarter)
	flags = d.flags
	used = d.get("used", {})
	super_like_available = d.super_like_available
	careers = d.get("careers", {})
	partner = d.get("partner", {})
	look = d.get("look", {})
	housing = d.get("housing", {"kind": "parents"})
	debts = d.get("debts", [])
	savings = int(d.get("savings", 0))
	investments = int(d.get("investments", 0))
	invest_bold = d.get("invest_bold", false)
	debt_years = int(d.get("debt_years", 0))
	fresh_start_until = int(d.get("fresh_start_until", 0))
	course = d.get("course", {})
	for entry in careers.values():  # JSON reads numbers back as floats
		for k in ["rank", "performance", "years", "meter"]:
			entry[k] = int(entry[k])
		for role in entry.coworkers:
			entry.coworkers[role].affinity = int(entry.coworkers[role].affinity)
	if partner.has("affinity"):
		partner.affinity = int(partner.affinity)
	for s in STATS:
		stats[s] = int(d.stats.get(s, stats.get(s, 50 if s in TRAITS else 0)))
