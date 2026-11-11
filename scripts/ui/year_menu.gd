class_name YearMenu
extends VBoxContainer
## Between-year menu (GDD §6): tabs unlock by age (§6.7), each action costs money and Stress.

signal acted

var db: ActionDB
var careers: CareerDB  # the "jobs" tab is the career menu (docs/CAREERS.md)
var finance: FinanceDB
var shop: Items
var tab := ""
var page := []  # career submenu path: [], ["find"], [slot, "advance"], [slot, "staff", role]
var tabs_row := HBoxContainer.new()
var info := Label.new()
var list := VBoxContainer.new()
var careers_rng := RandomNumberGenerator.new()


func _init(
	action_db: ActionDB,
	career_db: CareerDB = null,
	finance_db: FinanceDB = null,
	items: Items = null
) -> void:
	db = action_db
	shop = items
	careers = career_db
	finance = finance_db


func _ready() -> void:
	add_theme_constant_override("separation", 12)
	tabs_row.add_theme_constant_override("separation", 8)
	add_child(tabs_row)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	info.add_theme_font_size_override("font_size", 26)
	info.add_theme_color_override("font_color", Color(0.15, 0.15, 0.18))
	add_child(info)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list.add_theme_constant_override("separation", 8)
	scroll.add_child(list)
	add_child(scroll)


## Opens the menu for this year with a headline (the year-end results).
func open(headline: String) -> void:
	info.text = headline
	var tabs := ActionDB.tabs_at(GameState.age)
	if tab not in tabs:
		tab = tabs[0] if not tabs.is_empty() else ""
	if not page.is_empty() and page[0] in ["job", "special"] and not GameState.careers.has(page[0]):
		page = []  # the career ended between years
	_build()
	show()


func _build() -> void:
	for c in tabs_row.get_children() + list.get_children():
		c.queue_free()
	for t in ActionDB.tabs_at(GameState.age):
		var b := Button.new()
		b.text = ActionDB.TAB_NAMES[t]
		b.toggle_mode = true
		b.button_pressed = t == tab
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.add_theme_font_size_override("font_size", 26)
		b.pressed.connect(
			func():
				tab = t
				page = []
				_build()
		)
		tabs_row.add_child(b)
	if tab == "":
		_note("Too young for plans. Just grow.")
		return
	if tab == "jobs" and careers:
		_build_career()
		return
	if tab == "money" and finance:
		_build_money()
		return
	for a in db.available(tab, GameState.age, GameState):
		var b := Button.new()
		var cost := int(a.get("cost", 0))
		b.text = a.label + ("   $%d" % cost if cost else "")
		b.disabled = GameState.stats.money < cost
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size.y = 64
		b.add_theme_font_size_override("font_size", 26)
		b.pressed.connect(do_action.bind(a))
		list.add_child(b)
	if tab == "shop" and shop:
		for it in shop.available(GameState):
			_button(
				"%s   %s" % [it.label, Finance.money_text(int(it.price))],
				func(): _did(shop.buy(GameState, it)),
				not shop.can_buy(GameState, it)
			)


func _button(text: String, on_press: Callable, disabled := false) -> void:
	var b := Button.new()
	b.text = text
	b.disabled = disabled
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.custom_minimum_size.y = 64
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART  # long rows wrap, never widen the panel
	b.add_theme_font_size_override("font_size", 26)
	b.pressed.connect(on_press)
	list.add_child(b)


func _go(to: Array) -> void:
	page = to
	_build()


func _did(line: String) -> void:
	if line == "":
		return
	info.text = line
	acted.emit()
	if not page.is_empty() and page[0] in ["job", "special"] and not GameState.careers.has(page[0]):
		page = []
	_build()


## Career menu: your careers, then submenus to advance, deal with staff, or find other work.
func _build_career() -> void:
	if page.is_empty():
		for slot in ["job", "special"]:
			var e: Dictionary = GameState.careers.get(slot, {})
			if e.is_empty():
				continue
			_note(
				(
					"%s: %s  ·  performance %d"
					% [careers.by_id[e.id].label, CareerRules.title(e), e.performance]
				)
			)
			_button("  Advance your standing", _go.bind([slot, "advance"]))
			_button("  Staff", _go.bind([slot, "staff"]))
		if GameState.careers.is_empty():
			_note("No job yet.")
		_button("Look for work", _go.bind(["find"]))
		if finance and GameState.age >= Finance.ADULT_AGE:
			if GameState.course.is_empty():
				_button("Courses", _go.bind(["courses"]))
			else:
				var c: Dictionary = GameState.course
				_note("Studying %s: %d year(s) left" % [c.label, c.left])
		return
	_button("< Back", _go.bind(page.slice(0, -1) if page.size() > 2 else []))
	if page[0] == "courses":
		_build_courses()
		return
	if page[0] == "find":
		for c in careers.available(GameState):
			var held: Dictionary = GameState.careers.get(c.kind, {})
			var cost := int(c.get("cost", 0))
			var text: String = c.label + ("   $%d" % cost if cost else "")
			if GameState.age >= Finance.ADULT_AGE:
				var start := CareerRules.rank_pay(c.ranks[0], GameState.age)
				text += "   %s a year" % Finance.money_text(start)
			if held.get("id") == c.id:
				continue
			if not held.is_empty():
				text = "%s, leaving %s" % [text, careers.by_id[held.id].label]
			_button(
				text,
				func():
					_did(
						(
							"You start as %s." % c.ranks[0].title
							if CareerRules.apply(c, GameState, careers_rng)
							else ""
						)
					),
				GameState.stats.money < cost
			)
		return
	var slot: String = page[0]
	var e: Dictionary = GameState.careers[slot]
	if page[1] == "advance":
		_button("Work hard", func(): _did(CareerRules.work_hard(GameState, slot)))
		_button(
			"Ask for a promotion", func(): _did(CareerRules.ask_promotion(GameState, slot, careers))
		)
		_button("Quit", func(): _quit(slot))
	elif page.size() == 2:
		for role in Coworkers.ROLES:
			var cw: Dictionary = e.coworkers[role]
			_button(
				"%s (%s)  ·  %d" % [cw.name, role, cw.affinity], _go.bind([slot, "staff", role])
			)
	else:
		var role: String = page[2]
		for act in CareerRules.staff_acts(role):
			var cost := int(CareerRules.STAFF[act].get("cost", 0))
			_button(
				act.capitalize() + ("   $%d" % cost if cost else ""),
				func(): _did(CareerRules.staff(GameState, slot, role, act)),
				GameState.stats.money < cost
			)


func _build_courses() -> void:
	for c in finance.courses_open(GameState):
		var cost := int(c.yearly)
		var head := "%s  ·  %d yr  ·  %s a year" % [c.label, c.years, Finance.money_text(cost)]
		_button(head, func(): _enrol(c, false), GameState.stats.money < cost)
		if cost > 0:
			_button(
				"  On a student loan", func(): _enrol(c, true), not Finance.loan_open(GameState, c)
			)


func _enrol(c: Dictionary, on_loan: bool) -> void:
	page = []
	_did(Finance.enrol(GameState, c, on_loan))


## Money tab (docs/ADULT_MONEY.md): housing and property, savings, investments, debts.
func _build_money() -> void:
	if not page.is_empty():
		_button("< Back", _go.bind([]))
		_build_property()
		return
	var h: Dictionary = GameState.housing
	var home: String = {"parents": "With your parents", "rent": "Renting"}.get(h.kind, "")
	_note(home if home != "" else "%s, worth %s" % [h.label, Finance.money_text(h.value)])
	if h.kind == "parents":
		var cost := Finance.money_text(Finance.RENT)
		_button("Rent a place   %s a year" % cost, func(): _did(Finance.rent(GameState)))
	if h.kind == "own":
		_button("Sell the house", func(): _did(Finance.sell(GameState)))
	else:
		_button("Property", _go.bind(["property"]))
	var cash: int = GameState.stats.money
	_note("Savings %s" % Finance.money_text(GameState.savings))
	_button("  Save a quarter of your money", func(): _move(Finance.to_savings, cash / 4), cash < 4)
	_button("  Take it all out", func(): _take(Finance.from_savings), GameState.savings == 0)
	var mode := "Bold" if GameState.invest_bold else "Safe"
	_note("Investments %s  ·  %s" % [Finance.money_text(GameState.investments), mode])
	_button("  Invest a quarter", func(): _move(Finance.to_investments, cash / 4), cash < 4)
	_button("  Cash out", func(): _take(Finance.from_investments), GameState.investments == 0)
	_button(
		"  Switch to %s" % ("safe" if GameState.invest_bold else "bold"),
		_toggle_bold,
		not GameState.invest_bold and not Finance.can_invest_bold(GameState)
	)
	for d in GameState.debts:
		_note("%s  %s" % [String(d.kind).capitalize(), Finance.money_text(d.balance)])
		_button("  Pay what you can", func(): _did(Finance.pay_debt(GameState, d)), cash <= 0)
	if Finance.can_fresh_start(GameState, careers):
		_button("Fresh start", func(): _did(Finance.fresh_start(GameState)))


func _build_property() -> void:
	if not Finance.can_borrow(GameState):
		_note("The bank wants a job and a clean slate.")
	for house in finance.houses:
		if GameState.age < int(house.min_age):
			continue
		var line := (
			"%s  %s  ·  deposit %s"
			% [
				house.label,
				Finance.money_text(house.price),
				Finance.money_text(Finance.deposit(house)),
			]
		)
		var lent := Finance.can_afford(GameState, house, careers)
		if not lent:
			line += "  ·  needs pay %s" % Finance.money_text(Finance.house_cost(house) * 2)
		_button(line, func(): _buy(house), not (lent and Finance.can_buy(GameState, house)))


func _buy(house: Dictionary) -> void:
	page = []
	_did(Finance.buy(GameState, house))


func _move(move: Callable, amount: int) -> void:
	move.call(GameState, amount)
	_did("Done.")


func _take(move: Callable) -> void:
	move.call(GameState)
	_did("Done.")


func _toggle_bold() -> void:
	GameState.invest_bold = not GameState.invest_bold
	_did("Your investments are now %s." % ("bold" if GameState.invest_bold else "safe"))


func _quit(slot: String) -> void:
	var label: String = careers.by_id[GameState.careers[slot].id].label
	CareerRules.leave(GameState, slot, "quit")
	GameState.change_stat("stress", 2)
	_did("You quit the %s." % label.to_lower())


func _note(text: String) -> void:
	var l := Label.new()
	l.text = text
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", 26)
	l.add_theme_color_override("font_color", Color(0.4, 0.38, 0.35))
	list.add_child(l)


func do_action(a: Dictionary) -> void:
	if ActionDB.perform(a, GameState):
		var line := Family.act(a.get("do", ""), GameState, careers_rng)
		info.text = line if line != "" else a.get("result", a.label)
		acted.emit()
		_build()


## Everything the player could do right now (autoplay).
func choices() -> Array:
	var out := []
	for t in ActionDB.tabs_at(GameState.age):
		for a in db.available(t, GameState.age, GameState):
			if GameState.stats.money >= int(a.get("cost", 0)):
				out.append(a)
	return out
