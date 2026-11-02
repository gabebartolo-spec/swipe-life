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
var flags := {}
var super_like_available := true  # one per year (GDD §3.3)


func _ready() -> void:
	new_life()


func new_life() -> void:
	age = 0
	quarter = 0
	flags = {}
	super_like_available = true
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
		"super_like_available": super_like_available,
	}


func from_dict(d: Dictionary) -> void:
	age = int(d.age)
	quarter = int(d.quarter)
	flags = d.flags
	super_like_available = d.super_like_available
	for s in STATS:
		stats[s] = int(d.stats.get(s, stats[s]))
