# tests/test_chord_view.py
from views.subviews.chord_view import ChordView

def test_chord_view_initialization():
    view = ChordView()
    assert view.current_target is not None
    assert view.chord_name_text.value != ""
    assert view.fretboard_view.visible is False
