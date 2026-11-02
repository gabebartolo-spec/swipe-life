class_name Coworkers
extends RefCounted
## The four named people at every job: boss, rival, crush and friend. Each has an affinity
## (-100 hates you, 100 adores you). Story state such as dating the crush lives in "work_" flags,
## which CareerRules.leave clears with the job.

const ROLES := ["boss", "rival", "crush", "friend"]
const START_AFFINITY := {"boss": 0, "rival": -20, "crush": 10, "friend": 30}
const NAMES := [
	"Mia",
	"Jack",
	"Chloe",
	"Liam",
	"Zara",
	"Noah",
	"Ruby",
	"Kai",
	"Isla",
	"Leo",
	"Ava",
	"Finn",
	"Sienna",
	"Jai",
	"Olive",
	"Mason",
	"Priya",
	"Tom",
	"Lily",
	"Ezra",
	"Grace",
	"Sami",
	"Ivy",
	"Ned"
]


## Four distinct names, one per role.
static func generate(rng: RandomNumberGenerator) -> Dictionary:
	var pool := NAMES.duplicate()
	var out := {}
	for role in ROLES:
		var who: String = pool.pop_at(rng.randi() % pool.size())
		out[role] = {"name": who, "affinity": START_AFFINITY[role]}
	return out


static func change(coworkers: Dictionary, role: String, delta: int) -> void:
	if coworkers.has(role):
		var p: Dictionary = coworkers[role]
		p.affinity = clampi(int(p.affinity) + delta, -100, 100)
