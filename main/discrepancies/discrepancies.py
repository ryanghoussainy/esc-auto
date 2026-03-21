from collections import defaultdict
from fuzzywuzzy import fuzz

from .discrepancy_types.empty_timesheet import EmptyTimesheet
from .discrepancy_types.invalid_name import InvalidName
from .discrepancy_types.sign_in_extra_entry import SignInExtraEntry
from .discrepancy_types.timesheet_extra_entry import TimesheetExtraEntry


def format_entry(entry) -> str:
    event_suffix = " (event)" if entry.is_event else ""
    return f"{entry.date} | {entry.hours:.2f}h | ${entry.rate:.2f}/h{event_suffix}"


def rank_names_by_similarity(target_name: str, candidate_names: list[str]) -> list[str]:
    target = target_name.strip().lower()

    def score(candidate: str) -> int:
        candidate_normalized = candidate.strip().lower()
        return fuzz.token_sort_ratio(target, candidate_normalized)

    return sorted(candidate_names, key=lambda name: (-score(name), name.lower()))


def display_timesheet_discrepancies(discrepancies, progress_callback):
    invalid_names = [d for d in discrepancies if isinstance(d, InvalidName)]
    empty_timesheets = [d for d in discrepancies if isinstance(d, EmptyTimesheet)]
    timesheet_only = [d for d in discrepancies if isinstance(d, TimesheetExtraEntry)]
    signin_only = [d for d in discrepancies if isinstance(d, SignInExtraEntry)]

    progress_callback(f"Mismatches found: {len(discrepancies)}", "red")
    progress_callback("Summary by category:", "yellow")
    progress_callback(f"- Name issues: {len(invalid_names)}")
    progress_callback(f"- Empty timesheets: {len(empty_timesheets)}")
    progress_callback(f"- Extra in timesheet: {len(timesheet_only)}")
    progress_callback(f"- Missing from timesheet: {len(signin_only)}")

    if invalid_names:
        progress_callback("")
        progress_callback("Name issues to fix:", "yellow")
        for issue in sorted(invalid_names, key=lambda d: d.name.lower()):
            ranked_names = rank_names_by_similarity(issue.name, issue.sign_in_names)
            progress_callback(f"- '{issue.name}' is not in sign-in sheet")
            progress_callback(f"  Available names: {', '.join(ranked_names)}")

    if empty_timesheets:
        progress_callback("")
        progress_callback("Empty timesheets:", "yellow")
        for issue in sorted(empty_timesheets, key=lambda d: d.sheet_name.lower()):
            progress_callback(f"- {issue.sheet_name}")

    if timesheet_only:
        grouped = defaultdict(list)
        for issue in timesheet_only:
            grouped[issue.name].append(issue.entry)

        progress_callback("")
        progress_callback("Extra in timesheet (not found in sign-in):", "yellow")
        for name in sorted(grouped):
            entries = sorted(grouped[name], key=lambda e: (e.date, e.hours, e.rate, e.is_event))
            progress_callback(f"- {name} ({len(entries)} entries)")
            for entry in entries:
                progress_callback(f"  - {format_entry(entry)}")

    if signin_only:
        grouped = defaultdict(list)
        for issue in signin_only:
            grouped[issue.name].append(issue.entry)

        progress_callback("")
        progress_callback("Missing from timesheet (found in sign-in only):", "yellow")
        for name in sorted(grouped):
            entries = sorted(grouped[name], key=lambda e: (e.date, e.hours, e.rate, e.is_event))
            progress_callback(f"- {name} ({len(entries)} entries)")
            for entry in entries:
                progress_callback(f"  - {format_entry(entry)}")

def display_discrepancies(discrepancies, progress_callback):
    if not discrepancies:
        progress_callback("No mismatches found.", "green")
        return
    
    display_timesheet_discrepancies(discrepancies, progress_callback)
