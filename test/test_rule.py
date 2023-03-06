from src.generate import apply_rules
import unittest
import pandas as pd

rule = pd.read_csv("rules.csv")

class TestRules(unittest.TestCase):
    def test_rule1(self):
        old = [{'value': ('parts', 'Background', 'white'), 'trait_type': 'Background'},
               {'value': ('parts', 'First Letter', 'H'), 'trait_type': 'First Letter'},
               {'value': ('parts', 'Second Letter', 'A'), 'trait_type': 'Second Letter'}]
        should = [{'value': ('parts', 'Background', 'white'), 'trait_type': 'Background'}, 
                  {'value': ('parts', 'First Letter', 'H'), 'trait_type': 'First Letter'},  
                  {'value': ('parts', 'Second Letter', 'A'), 'trait_type': 'Second Letter'},]
        random_attr1 = apply_rules(old, rule)
        self.assertEqual(random_attr1[0], True)
        self.assertEqual(random_attr1[1], should)

    def test_rule2(self):
        old = [{'value': ('parts', 'Background', 'blue'), 'trait_type': 'Background'},
               {'value': ('parts', 'First Letter', 'C'), 'trait_type': 'First Letter'},
               {'value': ('parts', 'Second Letter', 'R'), 'trait_type': 'Second Letter'}]
        should = [{'value': ('parts', 'Background', 'blue'), 'trait_type': 'Background'}, 
                  {'value': ('parts', 'First Letter', 'B'), 'trait_type': 'First Letter'},  
                  {'value': ('parts', 'Second Letter', 'A'), 'trait_type': 'Second Letter'},]
        random_attr1 = apply_rules(old, rule)
        self.assertEqual(random_attr1[0], True)
        self.assertEqual(random_attr1[1], should)

    def test_rule3(self):
        old = [{'value': ('parts', 'Background', 'green'), 'trait_type': 'Background'},
               {'value': ('parts', 'First Letter', 'B'), 'trait_type': 'First Letter'},
               {'value': ('parts', 'Second Letter', 'A'), 'trait_type': 'Second Letter'}]
        should = ""
        random_attr1 = apply_rules(old, rule)
        self.assertEqual(random_attr1[0], False)
        self.assertEqual(random_attr1[1], should)

    def test_rule4(self):
        old = [{'value': ('parts', 'Background', 'black'), 'trait_type': 'Background'},
               {'value': ('parts', 'First Letter', '1'), 'trait_type': 'First Letter'},
               {'value': ('parts', 'Second Letter', 'empty'), 'trait_type': 'Second Letter'}]
        should = ""
        random_attr1 = apply_rules(old, rule)
        self.assertEqual(random_attr1[0], True)
        self.assertEqual(random_attr1[1], old)

if __name__ == '__main__':
    unittest.main()