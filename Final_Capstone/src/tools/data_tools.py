from pathlib import Path
import pandas as pd


class DataTools:
    def __init__(self, inventory_path='data/inventory.csv', purchases_path='data/purchases.csv'):
        self.inv_path = Path(inventory_path)
        self.purchases_path = Path(purchases_path)
        # ensure files exist
        if not self.inv_path.exists():
            self.inv_path.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(columns=['item','quantity','reorder_level','price','unit','avg_daily_sales']).to_csv(self.inv_path, index=False)
        if not self.purchases_path.exists():
            self.purchases_path.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(columns=['date','supplier','item','qty','price']).to_csv(self.purchases_path, index=False)


    def load_inventory(self):
        return pd.read_csv(self.inv_path)


    def save_inventory(self, df):
       df.to_csv(self.inv_path, index=False)


    def load_purchases(self):
        return pd.read_csv(self.purchases_path)


    def append_purchase(self, rec: dict):
        df = self.load_purchases()
        df = pd.concat([df, pd.DataFrame([rec])], ignore_index=True)
        df.to_csv(self.purchases_path, index=False)