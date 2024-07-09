# dlnstats.py
import pandas as pd
import requests
import json  # Import the json module
import matplotlib.pyplot as plt  # Import matplotlib for visualization

# ... existing code ...

def get_popular_tokens():
    url = "https://stats-api.dln.trade/api/TokenMetadata/popularTokens"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def get_all_time_statistics():
    url = "https://stats-api.dln.trade/api/Satistics/getAllTime"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# Example usage
if __name__ == "__main__":

    all_time_stats = get_all_time_statistics()
    print("All-Time Statistics:")
    print(json.dumps(all_time_stats, indent=4))  # Pretty-print the all-time statistics

    # Calculate and print the percentage of orders not filled
    created_orders = all_time_stats['createdOrdersCount']
    fulfilled_orders = all_time_stats['fulfilledOrdersCount']
    not_filled_orders = created_orders - fulfilled_orders
    not_filled_percentage = (not_filled_orders / created_orders) * 100

    print(f"Percentage of Orders Not Filled: {not_filled_percentage:.2f}%")

    # Additional calculations
    # Order fulfillment rate
    fulfillment_rate = (fulfilled_orders / created_orders) * 100
    print(f"Order Fulfillment Rate: {fulfillment_rate:.2f}%")

    # Average order value
    total_amount_given = all_time_stats['totalAmountGivenUsd']
    total_amount_taken = all_time_stats['totalAmountTakenUsd']
    avg_order_value_given = total_amount_given / created_orders
    avg_order_value_taken = total_amount_taken / created_orders

    print(f"Average Order Value Given: ${avg_order_value_given:.2f}")
    print(f"Average Order Value Taken: ${avg_order_value_taken:.2f}")

    # Protocol and affiliate fees as percentage of total amount given
    total_protocol_fee = all_time_stats['totalProtocolFeeUsd']
    total_affiliate_fee = all_time_stats['totalAffiliateFeeUsd']
    protocol_fee_percentage = (total_protocol_fee / total_amount_given) * 100
    affiliate_fee_percentage = (total_affiliate_fee / total_amount_given) * 100

    print(f"Protocol Fee Percentage: {protocol_fee_percentage:.2f}%")
    print(f"Affiliate Fee Percentage: {affiliate_fee_percentage:.2f}%")

    # Active orders percentage
    active_orders = all_time_stats['activeOrdersCount']
    active_orders_percentage = (active_orders / created_orders) * 100

    print(f"Active Orders Percentage: {active_orders_percentage:.2f}%")

    # Convert all_time_stats to DataFrame for EDA
    df = pd.DataFrame([all_time_stats])

    # Generate summary statistics
    print("\nSummary Statistics:")
    print(df.describe())

    # Visualize data
    plt.figure(figsize=(10, 6))

    # Bar plot for order counts
    plt.subplot(2, 1, 1)
    plt.bar(['Created Orders', 'Fulfilled Orders', 'Not Filled Orders'], 
            [created_orders, fulfilled_orders, not_filled_orders], color=['blue', 'green', 'red'])
    plt.title('Order Counts')
    plt.ylabel('Count')

    # Pie chart for order fulfillment
    plt.subplot(2, 1, 2)
    plt.pie([fulfilled_orders, not_filled_orders], labels=['Fulfilled Orders', 'Not Filled Orders'], 
            autopct='%1.1f%%', colors=['green', 'red'])
    plt.title('Order Fulfillment')

    plt.tight_layout()
    plt.show()

# ... existing code ...