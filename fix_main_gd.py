# -*- coding: utf-8 -*-
import os

content = """\
extends Node2D

# =====================================================================
# SUMERAGI - MVP-05
# ターン制対戦：何が何に勝つか
# =====================================================================

const WIN_W  : int    = 405
const WIN_H  : int    = 720
const N8N    : String = "https://okdsgr.app.n8n.cloud/webhook/"
const DESCENT_TIME : float = 180.0

enum Phase { TITLE, CPU_SPAWNING, PLAYER_INPUT, WAITING_JUDGE, BATTLE_SCENE, NEXT_ROUND }
var _phase : Phase = Phase.TITLE

var _http_judge   : HTTPRequest = null
var _http_counter : HTTPRequest = null
var _ui           : CanvasLayer = null

var _cpu_entity    : String = ""
var _cpu_entity_ja : String = ""
var _player_entity : String = ""
var _round         : int    = 0
var _player_score  : int    = 0
var _cpu_score     : int    = 0

var _descent_y     : float  = 0.0
var _descent_timer : float  = 0.0
var _cpu_lbl_node  : Label  = null

const FIRST_ENTITIES : Array = [
\t["frog",      "カエル"],
\t["cockroach", "ゴキブリ"],
\t["spider",    "クモ"],
\t["mouse",     "ネズミ"],
\t["crow",      "カラス"],
\t["jellyfish", "クラゲ"],
\t["centipede", "ムカデ"],
\t["wasp",      "スズメバチ"],
]

func _ready() -> void:
\tDisplayServer.window_set_size(Vector2i(WIN_W, WIN_H))
\tvar scr := DisplayServer.screen_get_size()
\tDisplayServer.window_set_position(Vector2i((scr.x - WIN_W) / 2, (scr.y - WIN_H) / 2))
\tRenderingServer.set_default_clear_color(Color(0.05, 0.05, 0.12))
\t_ui = $UI
\t_http_judge = HTTPRequest.new()
\t_http_judge.timeout = 30.0
\tadd_child(_http_judge)
\t_http_counter = HTTPRequest.new()
\t_http_counter.timeout = 30.0
\tadd_child(_http_counter)
\t_show_title()

func _process(delta: float) -> void:
\tif _phase == Phase.PLAYER_INPUT and is_instance_valid(_cpu_lbl_node):
\t\t_descent_timer += delta
\t\tvar progress := _descent_timer / DESCENT_TIME
\t\tprogress = clampf(progress, 0.0, 1.0)
\t\t_descent_y = -60.0 + (WIN_H + 60.0) * progress
\t\t_cpu_lbl_node.position.y = _descent_y
\t\tvar bar := _ui.get_node_or_null("TimeBar")
\t\tif bar and bar is ProgressBar:
\t\t\t(bar as ProgressBar).value = 1.0 - progress
\t\tif progress >= 1.0:
\t\t\t_on_time_up()

func _show_title() -> void:
\t_phase = Phase.TITLE
\t_clear_ui()
\tvar title := Label.new()
\ttitle.text = "AKINEMON"
\ttitle.add_theme_font_size_override("font_size", 64)
\ttitle.add_theme_color_override("font_color", Color(0.95, 0.88, 0.55))
\ttitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
\ttitle.position = Vector2(0, 240)
\ttitle.custom_minimum_size = Vector2(WIN_W, 0)
\t_ui.add_child(title)
\tvar sub := Label.new()
\tsub.text = "アキねもん"
\tsub.add_theme_font_size_override("font_size", 22)
\tsub.add_theme_color_override("font_color", Color(0.75, 0.68, 0.4, 0.85))
\tsub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
\tsub.position = Vector2(0, 328)
\tsub.custom_minimum_size = Vector2(WIN_W, 0)
\t_ui.add_child(sub)
\tvar desc := Label.new()
\tdesc.text = "おまかせあれ！たぶん当たる！"
\tdesc.add_theme_font_size_override("font_size", 15)
\tdesc.add_theme_color_override("font_color", Color(0.65, 0.7, 0.9, 0.8))
\tdesc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
\tdesc.position = Vector2(0, 390)
\tdesc.custom_minimum_size = Vector2(WIN_W, 0)
\t_ui.add_child(desc)
\tvar btn := Button.new()
\tbtn.text = "▶ ゲーム開始"
\tbtn.custom_minimum_size = Vector2(260, 64)
\tbtn.add_theme_font_size_override("font_size", 20)
\tbtn.position = Vector2((WIN_W - 260) / 2, 520)
\t_ui.add_child(btn)
\tbtn.pressed.connect(_start_game)

func _start_game() -> void:
\t_round = 0
\t_player_score = 0
\t_cpu_score = 0
\t_cpu_entity = ""
\t_cpu_entity_ja = ""
\t_next_cpu_turn("")

func _next_cpu_turn(player_won_entity: String) -> void:
\t_round += 1
\t_phase = Phase.CPU_SPAWNING
\t_clear_ui()
\tvar status := Label.new()
\tstatus.text = "ROUND %d  CPUが考えています…" % _round
\tstatus.add_theme_font_size_override("font_size", 22)
\tstatus.add_theme_color_override("font_color", Color(0.7, 0.75, 1.0))
\tstatus.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
\tstatus.position = Vector2(0, 300)
\tstatus.custom_minimum_size = Vector2(WIN_W, 0)
\t_ui.add_child(status)
\tif player_won_entity.is_empty():
\t\tvar pick : Array = FIRST_ENTITIES[randi() % FIRST_ENTITIES.size()]
\t\t_cpu_entity    = pick[0]
\t\t_cpu_entity_ja = pick[1]
\t\tawait get_tree().create_timer(1.2).timeout
\t\t_start_player_input_phase()
\telse:
\t\t_call_cpu_counter(player_won_entity)

func _call_cpu_counter(winner: String) -> void:
\tvar body := JSON.stringify({"winner": winner})
\tvar headers : PackedStringArray = ["Content-Type: application/json"]
\tif _http_counter.request_completed.is_connected(_on_counter_response):
\t\t_http_counter.request_completed.disconnect(_on_counter_response)
\t_http_counter.request_completed.connect(_on_counter_response, CONNECT_ONE_SHOT)
\t_http_counter.request(N8N + "cpu-counter", headers, HTTPClient.METHOD_POST, body)

func _on_counter_response(_r: int, code: int, _h: PackedStringArray, body: PackedByteArray) -> void:
\tvar text := body.get_string_from_utf8()
\tprint("[Counter] code=", code, " body=", text.substr(0, 100))
\tvar json = JSON.parse_string(text)
\tif json and json.has("entity"):
\t\t_cpu_entity    = str(json["entity"])
\t\t_cpu_entity_ja = str(json.get("entity_ja", _cpu_entity))
\telse:
\t\tvar pick : Array = FIRST_ENTITIES[randi() % FIRST_ENTITIES.size()]
\t\t_cpu_entity    = pick[0]
\t\t_cpu_entity_ja = pick[1]
\t_start_player_input_phase()

func _start_player_input_phase() -> void:
\t_phase = Phase.PLAYER_INPUT
\t_descent_timer = 0.0
\t_clear_ui()
\tvar score_lbl := Label.new()
\tscore_lbl.name = "ScoreLabel"
\tscore_lbl.text = "YOU %d - CPU %d | ROUND %d" % [_player_score, _cpu_score, _round]
\tscore_lbl.add_theme_font_size_override("font_size", 14)
\tscore_lbl.add_theme_color_override("font_color", Color(0.6, 0.65, 0.9, 0.85))
\tscore_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
\tscore_lbl.position = Vector2(0, 14)
\tscore_lbl.custom_minimum_size = Vector2(WIN_W, 0)
\t_ui.add_child(score_lbl)
\tvar bar := ProgressBar.new()
\tbar.name = "TimeBar"
\tbar.min_value = 0.0
\tbar.max_value = 1.0
\tbar.value = 1.0
\tbar.show_percentage = false
\tbar.custom_minimum_size = Vector2(WIN_W - 40, 10)
\tbar.position = Vector2(20, 40)
\t_ui.add_child(bar)
\t_cpu_lbl_node = Label.new()
\t_cpu_lbl_node.name = "CPUEntity"
\t_cpu_lbl_node.text = "👾 %s" % _cpu_entity_ja
\t_cpu_lbl_node.add_theme_font_size_override("font_size", 42)
\t_cpu_lbl_node.add_theme_color_override("font_color", Color(1.0, 0.45, 0.35))
\t_cpu_lbl_node.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
\t_cpu_lbl_node.custom_minimum_size = Vector2(WIN_W, 0)
\t_cpu_lbl_node.position = Vector2(0, -60.0)
\t_ui.add_child(_cpu_lbl_node)
\tvar hint := Label.new()
\thint.text = "「%s」に勝てるものを入力してください" % _cpu_entity_ja
\thint.add_theme_font_size_override("font_size", 16)
\thint.add_theme_color_override("font_color", Color(0.8, 0.85, 1.0))
\thint.autowrap_mode = TextServer.AUTOWRAP_WORD
\thint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
\thint.custom_minimum_size = Vector2(WIN_W - 40, 0)
\thint.position = Vector2(20, 560)
\t_ui.add_child(hint)
\tvar input := LineEdit.new()
\tinput.name = "PlayerInput"
\tinput.placeholder_text = "例: ヘビ、タカ、塩..."
\tinput.custom_minimum_size = Vector2(270, 52)
\tinput.add_theme_font_size_override("font_size", 18)
\tinput.position = Vector2(20, 618)
\t_ui.add_child(input)
\tvar btn := Button.new()
\tbtn.name = "SubmitBtn"
\tbtn.text = "決定"
\tbtn.custom_minimum_size = Vector2(80, 52)
\tbtn.add_theme_font_size_override("font_size", 18)
\tbtn.position = Vector2(300, 618)
\t_ui.add_child(btn)
\tbtn.pressed.connect(_on_player_submit)
\tvar cb := func(_t: String): _on_player_submit()
\tinput.text_submitted.connect(cb)

func _on_player_submit() -> void:
\tif _phase != Phase.PLAYER_INPUT:
\t\treturn
\tvar input_node := _ui.get_node_or_null("PlayerInput")
\tif input_node == null:
\t\treturn
\tvar text : String = (input_node as LineEdit).text.strip_edges()
\tif text.is_empty():
\t\treturn
\t_player_entity = text
\t_call_battle_judge()

func _on_time_up() -> void:
\t_cpu_score += 1
\t_show_battle_scene("TIME UP…", [
\t\t"時間切れ！",
\t\t"%s が降りてきてしまった…" % _cpu_entity_ja,
\t\t"CPUの勝利！",
\t], false)

func _call_battle_judge() -> void:
\t_phase = Phase.WAITING_JUDGE
\tvar btn := _ui.get_node_or_null("SubmitBtn")
\tif btn and btn is Button:
\t\t(btn as Button).disabled = true
\tvar inp := _ui.get_node_or_null("PlayerInput")
\tif inp and inp is LineEdit:
\t\t(inp as LineEdit).editable = false
\tvar body := JSON.stringify({"player": _player_entity, "cpu": _cpu_entity})
\tvar headers : PackedStringArray = ["Content-Type: application/json"]
\tif _http_judge.request_completed.is_connected(_on_judge_response):
\t\t_http_judge.request_completed.disconnect(_on_judge_response)
\t_http_judge.request_completed.connect(_on_judge_response, CONNECT_ONE_SHOT)
\t_http_judge.request(N8N + "battle-judge", headers, HTTPClient.METHOD_POST, body)

func _on_judge_response(_r: int, code: int, _h: PackedStringArray, body: PackedByteArray) -> void:
\tvar text := body.get_string_from_utf8()
\tprint("[Judge] code=", code, " body=", text.substr(0, 200))
\tvar json = JSON.parse_string(text)
\tif json == null or not json.has("winner"):
\t\t_show_battle_scene("エラー", ["判定に失敗しました。もう一度お試しください。"], false)
\t\treturn
\tvar player_wins : bool = str(json["winner"]) == "player"
\tvar scene : Array = []
\tif json.has("scene") and json["scene"] is Array:
\t\tscene = json["scene"]
\telse:
\t\tscene = [str(json.get("reason", ""))]
\tif player_wins:
\t\t_player_score += 1
\t\t_show_battle_scene("YOU WIN！", scene, true)
\telse:
\t\t_cpu_score += 1
\t\t_show_battle_scene("CPU WIN…", scene, false)

func _show_battle_scene(headline: String, scene_lines: Array, player_wins: bool) -> void:
\t_phase = Phase.BATTLE_SCENE
\t_clear_ui()
\tvar score_lbl := Label.new()
\tscore_lbl.text = "YOU %d - CPU %d" % [_player_score, _cpu_score]
\tscore_lbl.add_theme_font_size_override("font_size", 14)
\tscore_lbl.add_theme_color_override("font_color", Color(0.6, 0.65, 0.9, 0.85))
\tscore_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
\tscore_lbl.position = Vector2(0, 14)
\tscore_lbl.custom_minimum_size = Vector2(WIN_W, 0)
\t_ui.add_child(score_lbl)
\tvar h := Label.new()
\th.text = headline
\th.add_theme_font_size_override("font_size", 48)
\th.add_theme_color_override("font_color", Color(0.35, 1.0, 0.55) if player_wins else Color(1.0, 0.38, 0.38))
\th.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
\th.position = Vector2(0, 60)
\th.custom_minimum_size = Vector2(WIN_W, 0)
\t_ui.add_child(h)
\tvar match_lbl := Label.new()
\tmatch_lbl.text = "%s VS %s" % [_player_entity, _cpu_entity_ja]
\tmatch_lbl.add_theme_font_size_override("font_size", 20)
\tmatch_lbl.add_theme_color_override("font_color", Color(0.85, 0.88, 1.0, 0.9))
\tmatch_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
\tmatch_lbl.position = Vector2(0, 130)
\tmatch_lbl.custom_minimum_size = Vector2(WIN_W, 0)
\t_ui.add_child(match_lbl)
\tvar y := 210.0
\tfor i : int in scene_lines.size():
\t\tvar line_lbl := Label.new()
\t\tline_lbl.text = str(scene_lines[i])
\t\tline_lbl.add_theme_font_size_override("font_size", 18)
\t\tline_lbl.add_theme_color_override("font_color", Color(0.88, 0.92, 1.0))
\t\tline_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD
\t\tline_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
\t\tline_lbl.custom_minimum_size = Vector2(WIN_W - 40, 0)
\t\tline_lbl.position = Vector2(20, y)
\t\tline_lbl.modulate.a = 0.0
\t\t_ui.add_child(line_lbl)
\t\tvar tw := create_tween()
\t\ttw.tween_interval(float(i) * 0.8)
\t\ttw.tween_property(line_lbl, "modulate:a", 1.0, 0.4)
\t\ty += 70.0
\tvar next_btn := Button.new()
\tnext_btn.text = "次のラウンド ▶" if player_wins else "続ける ▶"
\tnext_btn.custom_minimum_size = Vector2(260, 60)
\tnext_btn.add_theme_font_size_override("font_size", 18)
\tnext_btn.position = Vector2((WIN_W - 260) / 2, 612)
\tnext_btn.modulate.a = 0.0
\t_ui.add_child(next_btn)
\tvar wait_time := float(scene_lines.size()) * 0.8 + 0.4
\tvar tw2 := create_tween()
\ttw2.tween_interval(wait_time)
\ttw2.tween_property(next_btn, "modulate:a", 1.0, 0.3)
\tif player_wins:
\t\tnext_btn.pressed.connect(func(): _next_cpu_turn(_player_entity))
\telse:
\t\tnext_btn.pressed.connect(func(): _next_cpu_turn(""))

func _clear_ui() -> void:
\tfor c : Node in _ui.get_children():
\t\tc.queue_free()
\t_cpu_lbl_node = null
"""

target = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts', 'main.gd')
target = os.path.normpath(target)

# スクリプトと同じフォルダにmain.gdがない場合はカレントディレクトリのscripts/に書く
if not os.path.exists(os.path.dirname(target)):
    target = os.path.join('scripts', 'main.gd')

with open(target, 'w', encoding='utf-8') as f:
    f.write(content)

print('Written to:', target)
print('Lines:', content.count('\n'))
