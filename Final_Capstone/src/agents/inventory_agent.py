import pandas as pd
import os
from datetime import datetime
from tools.data_tools import DataTools
from tools.whatsapp_tool import WhatsAppTool
from utils.forecast import simple_forecast

SUPPLIER_PHONE = os.getenv('SUPPLIER_PHONE', 'whatsapp:+918582945056')


class InventoryAgent:
    def __init__(self, data_path='data/inventory.csv', orders_path='data/orders.csv'):
        self.dt = DataTools(inventory_path=data_path)
        self.whatsapp = WhatsAppTool()
        self.orders_path = orders_path
        self._ensure_orders_file()

    def _ensure_orders_file(self):
        """Create orders file if it doesn't exist"""
        if not os.path.exists(self.orders_path):
            os.makedirs(os.path.dirname(self.orders_path), exist_ok=True)
            df = pd.DataFrame(columns=['order_id', 'timestamp', 'item', 'qty', 'unit', 'status', 'supplier_phone'])
            df.to_csv(self.orders_path, index=False)

    def _save_order(self, orders, supplier_phone, status='sent'):
        """Save order to CSV"""
        try:
            order_id = datetime.now().strftime('%Y%m%d%H%M%S')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            records = []
            for order in orders:
                records.append({
                    'order_id': order_id,
                    'timestamp': timestamp,
                    'item': order['item'],
                    'qty': order['qty'],
                    'unit': order.get('unit', ''),
                    'status': status,
                    'supplier_phone': supplier_phone
                })

            df_new = pd.DataFrame(records)

            # Append to existing orders
            if os.path.exists(self.orders_path):
                df_existing = pd.read_csv(self.orders_path)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = df_new

            df_combined.to_csv(self.orders_path, index=False)
            return order_id
        except Exception as e:
            print(f"Error saving order: {e}")
            return None

    def get_order_history(self, limit=50):
        """Retrieve recent order history"""
        try:
            if os.path.exists(self.orders_path):
                df = pd.read_csv(self.orders_path)
                return df.tail(limit).to_dict('records')
            return []
        except Exception as e:
            print(f"Error loading order history: {e}")
            return []

    def identify_low_stock(self, df: pd.DataFrame):
        # If reorder_level column exists, use it. Else threshold 20% of max
        if 'reorder_level' in df.columns:
            return df[df['quantity'] <= df['reorder_level']]
        else:
            max_qty = df['quantity'].max() if not df.empty else 0
            return df[df['quantity'] <= 0.2 * max_qty]

    def create_order_list(self, df_low: pd.DataFrame, days_ahead=3):
        orders = []
        for _, r in df_low.iterrows():
            avg = r.get('avg_daily_sales', None)
            demand = simple_forecast(avg if pd.notna(avg) else 1, days_ahead)
            qty_needed = max(demand - int(r['quantity']), 0)
            if qty_needed > 0:
                orders.append({'item': r['item'], 'qty': qty_needed, 'unit': r.get('unit', '')})
        return orders

    def build_message(self, orders, store_name='My Store'):
        if not orders:
            return 'No order needed.'
        lines = [f'Hi, this is {store_name}. Please send the following items:']
        for o in orders:
            lines.append(f"- {o['item']} : {o['qty']} {o.get('unit', '')}")
        lines.append('Thanks')
        return '\n'.join(lines)

    def preview_order(self, days_ahead=3, store_name='My Store'):
        """Preview order without sending"""
        df = self.dt.load_inventory()
        low = self.identify_low_stock(df)
        if low.empty:
            return {'status': 'no_items', 'message': 'No items low on stock.', 'orders': []}
        orders = self.create_order_list(low, days_ahead)
        if not orders:
            return {'status': 'no_order', 'message': 'No order required after forecasting.', 'orders': []}
        msg = self.build_message(orders, store_name)
        return {'status': 'preview', 'message': msg, 'orders': orders}

    def send_confirmed_order(self, orders, store_name='My Store', supplier_phone=SUPPLIER_PHONE):
        """Send the confirmed order and save to history"""
        if not orders:
            return {'status': 'error', 'message': 'No orders to send'}

        msg = self.build_message(orders, store_name)
        resp = self.whatsapp.send(supplier_phone, msg)

        # Save order to history
        order_id = self._save_order(orders, supplier_phone, status='sent')

        return {
            'status': 'sent',
            'message': 'Order sent successfully',
            'orders': orders,
            'order_id': order_id,
            'whatsapp_response': resp
        }

    def create_and_send_order(self, days_ahead=3, store_name='My Store', supplier_phone=SUPPLIER_PHONE):
        """Legacy method - generates and sends immediately"""
        df = self.dt.load_inventory()
        low = self.identify_low_stock(df)
        if low.empty:
            return 'No items low on stock.', []
        orders = self.create_order_list(low, days_ahead)
        if not orders:
            return 'No order required after forecasting.', []
        msg = self.build_message(orders, store_name)
        resp = self.whatsapp.send(supplier_phone, msg)

        # Save order to history
        self._save_order(orders, supplier_phone, status='sent')

        return msg, orders