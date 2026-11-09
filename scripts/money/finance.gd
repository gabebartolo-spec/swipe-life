class_name Finance
extends RefCounted
## Adult money from 18 (docs/ADULT_MONEY.md): housing, cost of living, debts, savings, investments
## and courses. Year end runs after careers have paid. Numbers scale from the entry salary E.

const E := 30000
const ADULT_AGE := 18
const RENT := int(0.35 * E)
const LIVING := int(0.25 * E)
const LOAN_RATE := 0.10
const SAVINGS_RATE := 0.02
const REPOSSESS_AFTER := 3  # years in debt
const DEPOSIT := 0.10
const MORTGAGE_YEARS := 25
const MORTGAGE_RATE := 0.04  # placeholder until balance (M13)
const STUDENT_RATE := 0.02  # placeholder until balance (M13)
const STUDENT_THRESHOLD := E  # repaid only on pay above this; placeholder
const STUDENT_SHARE := 0.05  # of yearly pay; placeholder
const STUDENT_WRITE_OFF := 40  # years
const FRESH_START_YEARS := 7
const FRESH_START_OVER_PAY := 3
const HOME_FROM := 22  # living with parents starts to cost Happiness and family
const SAFE := [-0.02, 0.06]
const BOLD := [-0.30, 0.30]
const BOLD_SMARTS := 40
const COURSE_SMARTS := 4
const COURSE_STRESS := 3
const COURSE_FAIL := 0.10  # less 1% per 10 Smarts above 50
const BUDGET := {"frugal": [0.8, -1], "spender": [1.2, 1]}  # living cost scale, Happiness a year


static func money_text(m: int) -> String:
	var digits := str(absi(m))
	for i in range(digits.length() - 3, 0, -3):
		digits = digits.insert(i, ",")
	return ("-$" if m < 0 else "$") + digits


static func total_debt(state) -> int:
	var out := 0
	for d in state.debts:
		out += int(d.balance)
	return out


static func yearly_pay(state, db: CareerDB) -> int:
	var out := 0
	for slot in state.careers:
		var entry: Dictionary = state.careers[slot]
		if db.by_id.has(entry.id):
			out += CareerRules.rank_pay(db.by_id[entry.id].ranks[int(entry.rank)], state.age)
	return maxi(out, 0)


static func can_borrow(state) -> bool:
	return state.careers.has("job") and not state.flags.has("fresh_start")


static func can_fresh_start(state, db: CareerDB) -> bool:
	var debt := 0
	for d in state.debts:
		if d.kind == "loan":
			debt += int(d.balance)
	return debt > 0 and total_debt(state) > FRESH_START_OVER_PAY * yearly_pay(state, db)


## One net Money block (cost of living, debts, growth, below-zero check). Returns result lines.
static func year_end(state, db: CareerDB, rng: RandomNumberGenerator) -> Array:
	var lines := []
	if state.age < ADULT_AGE:
		return lines
	var before: int = state.stats.money
	if yearly_pay(state, db) <= 0:
		lines.append("No income this year.")
	_course_year(state, rng, lines)
	_cost_of_living(state, lines)
	Family.year_end(state, rng, lines)
	_debt_year(state, db)
	_growth(state, rng, lines)
	if state.stats.money < 0:
		_add_debt(state, "loan", -state.stats.money, LOAN_RATE, 0)
		state.stats.money = 0
		state.change_stat("stress", 3)
		lines.append("You ended the year short. It's now a loan at 10%.")
	state.debt_years = state.debt_years + 1 if _has_loan(state) else 0
	if state.debt_years > REPOSSESS_AFTER and state.housing.kind == "own":
		_repossess(state, lines)
	if state.flags.has("fresh_start") and state.age >= int(state.fresh_start_until):
		state.flags.erase("fresh_start")
	lines.append("Money this year: %s" % Finance.money_text(state.stats.money - before))
	return lines


static func _cost_of_living(state, lines: Array) -> void:
	var kind: String = state.housing.kind
	if kind == "parents":
		if state.age >= HOME_FROM:
			state.change_stat("happiness", -2)
			state.change_stat("relationships", -2)
			lines.append("Still in your childhood bedroom.")
		return
	var living := float(LIVING)
	for style in BUDGET:
		if state.flags.has(style):
			living *= BUDGET[style][0]
			state.change_stat("happiness", BUDGET[style][1])
	state.change_stat("money", -int(living))
	if kind == "rent":
		state.change_stat("money", -RENT)
	else:
		state.change_stat("money", -int(state.housing.upkeep))
		state.housing.value = int(state.housing.value * (1.0 + state.housing.growth))


static func _debt_year(state, db: CareerDB) -> void:
	var pay := yearly_pay(state, db)
	for d in state.debts.duplicate():
		d.balance = int(d.balance * (1.0 + d.rate))
		var due := int(d.payment)
		if d.kind == "student":
			due = int(pay * STUDENT_SHARE) if pay > STUDENT_THRESHOLD else 0
			if state.age - int(d.taken) >= STUDENT_WRITE_OFF:
				state.debts.erase(d)
				continue
		elif d.kind == "loan":
			due = mini(maxi(state.stats.money, 0), int(d.balance))
		due = mini(due, int(d.balance))
		state.change_stat("money", -due)  # a missed payment goes below zero, then to a loan
		d.balance = int(d.balance) - due
		if d.balance <= 0:
			state.debts.erase(d)


static func _growth(state, rng: RandomNumberGenerator, lines: Array) -> void:
	state.savings = int(state.savings * (1.0 + SAVINGS_RATE))
	if state.investments <= 0:
		return
	var band: Array = BOLD if state.invest_bold else SAFE
	var change := int(state.investments * rng.randf_range(band[0], band[1]))
	state.investments += change
	if change != 0:
		lines.append(
			"Your investments went %s $%d." % ["up" if change > 0 else "down", absi(change)]
		)


static func _has_loan(state) -> bool:
	return state.debts.any(func(d): return d.kind == "loan")


static func _add_debt(state, kind: String, amount: int, rate: float, payment: int) -> void:
	for d in state.debts:
		if d.kind == kind and kind != "mortgage":
			d.balance = int(d.balance) + amount
			return
	state.debts.append(
		{"kind": kind, "balance": amount, "rate": rate, "payment": payment, "taken": state.age}
	)


static func _repossess(state, lines: Array) -> void:
	_clear_mortgage(state)
	state.housing = {"kind": "rent"}
	state.flags["moved_out"] = true
	state.change_stat("happiness", -10)
	state.change_stat("stress", 10)
	lines.append("The bank took the house. You're renting again.")


static func _clear_mortgage(state) -> int:
	var owed := 0
	for d in state.debts.duplicate():
		if d.kind == "mortgage":
			owed += int(d.balance)
			state.debts.erase(d)
	return owed


# Housing ----------------------------------------------------------------------------------------


static func rent(state) -> String:
	if state.housing.kind != "parents":
		return ""
	state.housing = {"kind": "rent"}
	state.flags["moved_out"] = true
	state.change_stat("happiness", 3)
	state.change_stat("stress", 2)
	return "You rent a place of your own."


## Equal yearly payment that clears `amount` at `rate` over `years`.
static func mortgage_payment(amount: int) -> int:
	var f := pow(1.0 + MORTGAGE_RATE, MORTGAGE_YEARS)
	return ceili(amount * MORTGAGE_RATE * f / (f - 1.0))


static func deposit(house: Dictionary) -> int:
	return int(house.price * DEPOSIT)


static func can_buy(state, house: Dictionary) -> bool:
	return (
		state.housing.kind != "own"
		and state.age >= int(house.min_age)
		and can_borrow(state)
		and state.stats.money >= deposit(house)
	)


static func buy(state, house: Dictionary) -> String:
	if not can_buy(state, house):
		return ""
	var dep := deposit(house)
	var owed := int(house.price) - dep
	state.change_stat("money", -dep)
	state.change_stat("stress", 4)
	state.change_stat("happiness", 6)
	_add_debt(state, "mortgage", owed, MORTGAGE_RATE, mortgage_payment(owed))
	state.housing = {
		"kind": "own",
		"house": house.id,
		"label": house.label,
		"value": int(house.price),
		"upkeep": int(house.upkeep),
		"growth": float(house.growth),
	}
	state.flags["moved_out"] = true
	return "You bought the %s." % String(house.label).to_lower()


static func sell(state) -> String:
	if state.housing.kind != "own":
		return ""
	var equity: int = int(state.housing.value) - _clear_mortgage(state)
	state.change_stat("money", equity)
	state.change_stat("stress", 2)
	var label: String = state.housing.label
	state.housing = {"kind": "rent"}
	return "You sold the %s. %s after the bank." % [label.to_lower(), Finance.money_text(equity)]


# Money moves ------------------------------------------------------------------------------------


static func to_savings(state, amount: int) -> void:
	amount = mini(amount, state.stats.money)
	state.change_stat("money", -amount)
	state.savings += amount


static func from_savings(state) -> void:
	state.change_stat("money", state.savings)
	state.savings = 0


static func to_investments(state, amount: int) -> void:
	amount = mini(amount, state.stats.money)
	state.change_stat("money", -amount)
	state.investments += amount


static func from_investments(state) -> void:
	state.change_stat("money", state.investments)
	state.investments = 0


static func can_invest_bold(state) -> bool:
	return state.stats.smarts >= BOLD_SMARTS


static func pay_debt(state, debt: Dictionary) -> String:
	var amount := mini(state.stats.money, int(debt.balance))
	if amount <= 0:
		return ""
	state.change_stat("money", -amount)
	state.change_stat("stress", -2)
	debt.balance = int(debt.balance) - amount
	if debt.balance <= 0:
		state.debts.erase(debt)
	return "You paid $%d off your %s." % [amount, debt.kind]


static func fresh_start(state) -> String:
	for d in state.debts.duplicate():
		if d.kind == "loan":
			state.debts.erase(d)
	state.debt_years = 0
	state.flags["fresh_start"] = true
	state.fresh_start_until = state.age + FRESH_START_YEARS
	state.change_stat("stress", -10)
	state.change_stat("happiness", -5)
	return "Your loans are gone. No bank will lend to you for 7 years."


# Courses ----------------------------------------------------------------------------------------


static func fail_chance(state) -> float:
	var bonus := maxf(state.stats.smarts - 50, 0.0) / 10.0 * 0.01
	return maxf(COURSE_FAIL - bonus, 0.0)


static func enrol(state, course: Dictionary, on_loan: bool) -> String:
	if not state.course.is_empty():
		return ""
	if not on_loan and state.stats.money < int(course.yearly):
		return ""
	state.course = {
		"id": course.id,
		"label": course.label,
		"flag": course.flag,
		"yearly": int(course.yearly),
		"left": int(course.years),
		"on_loan": on_loan,
	}
	return "You enrolled: %s." % course.label


## A year of study: cost, +Smarts, +Stress, and a chance of failing (the year is repeated).
static func _course_year(state, rng: RandomNumberGenerator, lines: Array) -> void:
	var c: Dictionary = state.course
	if c.is_empty():
		return
	if c.on_loan:
		_add_debt(state, "student", int(c.yearly), STUDENT_RATE, 0)
	else:
		state.change_stat("money", -int(c.yearly))
	state.change_stat("smarts", COURSE_SMARTS)
	state.change_stat("stress", COURSE_STRESS)
	if rng.randf() < fail_chance(state):
		state.change_stat("happiness", -3)
		lines.append("You failed the year of %s. Same again." % c.label)
		return
	c.left = int(c.left) - 1
	if c.left <= 0:
		state.flags[c.flag] = true
		lines.append("You finished: %s." % c.label)
		state.course = {}
