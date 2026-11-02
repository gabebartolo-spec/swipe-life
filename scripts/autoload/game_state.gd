extends Node
## One life's state: age, quarter, stats, flags and the yearly super like (GDD §2–§4).

const STATS := [
	"health", "happiness", "money", "career", "relationships", "smarts", "looks", "karma", "stress"
]
const HIDDEN_STATS := ["karma"]  # GDD §4.4
const UNBOUNDED_STATS := ["money"]  # GDD §4.3: every other stat is 0–100

var age := 0
var quarter := 0  # 0–3: which of the year's 4 cards is next (GDD §2.1)
var stats := {}
var flags := {}  # also holds illnesses (LifeRules.ILLNESSES)
var used := {}  # card ids drawn this life ("once" cards never repeat)
var super_like_available := true  # one per year (GDD §3.3)
var careers := {}  # slot ("job" / "special") -> entry; see CareerRules
var partner := {}  # {} = single, else {name, affinity, met}; outlives the job it came from


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
	stats = {}
	for s in STATS:
		stats[s] = 0 if s in UNBOUNDED_STATS or s == "stress" else 50


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
	}


func from_dict(d: Dictionary) -> void:
	age = int(d.age)
	quarter = int(d.quarter)
	flags = d.flags
	used = d.get("used", {})
	super_like_available = d.super_like_available
	careers = d.get("careers", {})
	partner = d.get("partner", {})
	for entry in careers.values():  # JSON reads numbers back as floats
		for k in ["rank", "performance", "years", "meter"]:
			entry[k] = int(entry[k])
		for role in entry.coworkers:
			entry.coworkers[role].affinity = int(entry.coworkers[role].affinity)
	if partner.has("affinity"):
		partner.affinity = int(partner.affinity)
	for s in STATS:
		stats[s] = int(d.stats.get(s, stats.get(s, 0)))
