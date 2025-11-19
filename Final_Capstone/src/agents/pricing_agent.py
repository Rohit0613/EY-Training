from tools.data_tools import DataTools
import pandas as pd


class PricingAgent:
    def __init__(self, data_path='data/inventory.csv'):
        self.dt = DataTools(inventory_path=data_path)


    def run_pricing_rules(self):
        df = self.dt.load_inventory()
        changes = []
        for idx, row in df.iterrows():
            qty = float(row.get('quantity', 0))
            base = float(row.get('price', 0.0))
            reorder = float(row.get('reorder_level', base*0 if base else 10))
        # Overstock -> discount
            if qty > reorder * 2:
                new = round(base * 0.9, 2)
                if new != base:
                    changes.append({'item': row['item'], 'old': base, 'new': new, 'reason': 'overstock_discount'})
                    df.at[idx, 'price'] = new
            elif qty <= reorder:
                new = round(base * 1.05, 2)
                if new != base:
                    changes.append({'item': row['item'], 'old': base, 'new': new, 'reason': 'low_stock_markup'})
                    df.at[idx, 'price'] = new
        if changes:
            self.dt.save_inventory(df)
        return changes


    def generate_offer_message(self, offers):
        lines = ['🔥 Today\'s Offers:']
        for o in offers:
            lines.append(f"{o['item']}: ₹{o['new']} (was ₹{o['old']})")
        return ''.join(lines)