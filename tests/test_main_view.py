# tests/test_main_view.py
"""Unit tests for the MainView layout container."""

from views.main_view import MainView

def test_main_view_initialization():
    view = MainView()
    assert view.scale_view is not None
    assert view.chord_view is not None
    assert view.metronome_view is not None
    assert len(view.subviews) == 3

def test_main_view_navigation():
    view = MainView()

    # Simulate selecting Chords (index 1)
    class DummyEvent:
        class Control:
            selected_index = 1
        control = Control()

    view._on_navigation_change(DummyEvent())
    assert view.content_area.content == view.chord_view
