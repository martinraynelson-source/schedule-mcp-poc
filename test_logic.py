import unittest
from server import get_sections_by_term, get_schedule_conflicts, find_available_rooms

class ScheduleTests(unittest.TestCase):
    def test_sections(self):
        self.assertEqual(get_sections_by_term('2027-SPRING')['count'], 4)
    def test_conflicts(self):
        result = get_schedule_conflicts('2027-SPRING')
        self.assertEqual(result['count'], 2)
        self.assertEqual({tuple(c['sections']) for c in result['conflicts']}, {('BIO101-01','CHEM101-01'),('BIO101-01','BIO201-01')})
    def test_rooms(self):
        result = find_available_rooms('2027-SPRING','MON','09:30','10:30',30)
        self.assertEqual([r['id'] for r in result['rooms']], ['R201'])
    def test_invalid_time(self):
        with self.assertRaises(ValueError):
            find_available_rooms('2027-SPRING','MON','11:00','10:00')

if __name__ == '__main__':
    unittest.main()
