from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP('Schedule MCP')

ROOMS = [
    {'id': 'R101', 'capacity': 40},
    {'id': 'R102', 'capacity': 30},
    {'id': 'R201', 'capacity': 60},
]
SECTIONS = [
    {'id': 'BIO101-01', 'term': '2027-SPRING', 'course': 'BIO101', 'instructor': 'I001', 'room': 'R101', 'day': 'MON', 'start': '09:00', 'end': '10:15', 'enrollment': 35},
    {'id': 'CHEM101-01', 'term': '2027-SPRING', 'course': 'CHEM101', 'instructor': 'I002', 'room': 'R101', 'day': 'MON', 'start': '09:30', 'end': '10:45', 'enrollment': 28},
    {'id': 'BIO201-01', 'term': '2027-SPRING', 'course': 'BIO201', 'instructor': 'I001', 'room': 'R102', 'day': 'MON', 'start': '10:00', 'end': '11:15', 'enrollment': 25},
    {'id': 'ENG101-01', 'term': '2027-SPRING', 'course': 'ENG101', 'instructor': 'I003', 'room': 'R201', 'day': 'MON', 'start': '11:00', 'end': '12:15', 'enrollment': 45},
    {'id': 'BIO101-02', 'term': '2027-FALL', 'course': 'BIO101', 'instructor': 'I001', 'room': 'R101', 'day': 'TUE', 'start': '09:00', 'end': '10:15', 'enrollment': 32},
]

def overlaps(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    return a_start < b_end and b_start < a_end

@mcp.tool()
def get_sections_by_term(term_id: str) -> dict:
    """List course sections for a term such as 2027-SPRING."""
    matches = [s for s in SECTIONS if s['term'] == term_id]
    return {'term_id': term_id, 'count': len(matches), 'sections': matches}

@mcp.tool()
def get_schedule_conflicts(term_id: str) -> dict:
    """Find overlapping room or instructor assignments in a term."""
    sections = [s for s in SECTIONS if s['term'] == term_id]
    conflicts = []
    for i, a in enumerate(sections):
        for b in sections[i+1:]:
            if a['day'] != b['day'] or not overlaps(a['start'], a['end'], b['start'], b['end']):
                continue
            types = []
            if a['room'] == b['room']:
                types.append('room')
            if a['instructor'] == b['instructor']:
                types.append('instructor')
            if types:
                conflicts.append({'sections': [a['id'], b['id']], 'types': types, 'day': a['day']})
    return {'term_id': term_id, 'count': len(conflicts), 'conflicts': conflicts}

@mcp.tool()
def find_available_rooms(term_id: str, day: str, start: str, end: str, minimum_capacity: int = 0) -> dict:
    """Find rooms free for a requested term, day, time window, and capacity. Times are HH:MM (24-hour)."""
    if day not in {'MON','TUE','WED','THU','FRI','SAT','SUN'}:
        raise ValueError('day must be MON, TUE, WED, THU, FRI, SAT, or SUN')
    try:
        start_time = datetime.strptime(start, '%H:%M').time()
        end_time = datetime.strptime(end, '%H:%M').time()
    except ValueError as exc:
        raise ValueError('Times must be HH:MM (24-hour)') from exc
    if start_time >= end_time:
        raise ValueError('start must precede end')
    if minimum_capacity < 0:
        raise ValueError('minimum_capacity must be nonnegative')
    occupied = {s['room'] for s in SECTIONS if s['term'] == term_id and s['day'] == day and overlaps(start, end, s['start'], s['end'])}
    available = [r for r in ROOMS if r['id'] not in occupied and r['capacity'] >= minimum_capacity]
    return {'term_id': term_id, 'day': day, 'start': start, 'end': end, 'rooms': available, 'count': len(available)}

if __name__ == '__main__':
    mcp.run(transport='stdio')
