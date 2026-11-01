from .events import load_events


def event_menu(request):
    """Expose le menu dynamique à tous les templates."""
    return {"events": load_events()}
