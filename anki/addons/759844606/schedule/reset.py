from ..utils import *
from anki.utils import ids2str


def clear_custom_data(did):
    if not askUser(
        """Clear custom data in all cards?
    The custom scheduling of FSRS4Anki stored memory state in custom data.
    It is unused when you enable the built-in FSRS.
    Are you sure?"""
    ):
        return

    cards = mw.col.db.list(
        """
            SELECT id
            FROM cards
            WHERE data != '' 
            AND json_extract(data, '$.cd') IS NOT NULL
        """
    )

    cnt = 0
    reset_cards = []
    start_time = time.time()
    undo_entry = mw.col.add_custom_undo_entry("Clear custom data")
    for cid in cards:
        card = mw.col.get_card(cid)
        card.custom_data = ""
        reset_cards.append(card)
        cnt += 1

    mw.col.update_cards(reset_cards)
    mw.col.merge_undo_entries(undo_entry)
    tooltip(f"""{cnt} cards cleared in {time.time() - start_time:.2f} seconds.""")
    mw.reset()


def clear_manual_rescheduling(did):
    if not askUser(
        'This option removes revlog entries generated by "Set due date" and "Reschedule cards on change" '
        + "that immediately precede another manual or reschedule entry.\n\n"
        + "This action cannot be undone. Do you want to continue?"
    ):
        return

    if not ask_one_way_sync():
        return

    revlog_ids = mw.col.db.list(
        """
        SELECT cur.id
        FROM revlog as cur
        WHERE cur.type >= 4
        AND cur.factor <> 0
        AND (
        SELECT type
        FROM revlog
        WHERE id = (
                SELECT min(id)
                FROM revlog
                WHERE id > cur.id
                AND cid == cur.cid
            )
        ) >= 4
    """
    )
    cnt = len(revlog_ids)
    mw.col.db.execute(f"DELETE FROM revlog WHERE id IN {ids2str(revlog_ids)}")
    col_set_modified()
    tooltip(f"{cnt} review logs deleted.")
    mw.reset()