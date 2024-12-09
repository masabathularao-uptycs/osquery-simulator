import numpy as np
from scipy.optimize import root_scalar
import math
import sys

def softmax(x, base):
    """Custom softmax function with custom base."""
    e_x = base ** np.array(x)  # Exponentiate with the custom base
    y = list(e_x * 100 / e_x.sum(axis=0))
    # print(y)
    y= [0.0 if np.isnan(x) else x for x in y]
    return y


def find_optimal_exponent(customers, target_load_percentage, target_customer_ratio):
    # Indices defining the cut-off for the first target_customer_ratio percentage of customers
    cutoff_idx = math.floor(customers * target_customer_ratio)  # Cut-off index for the first X% customers
    customer_indices = list(range(1, customers + 1))
    # print("cutoff_idx : ",cutoff_idx)
    # Define the optimization target function
    def objective_function(base):
        y = softmax(customer_indices, base)  # Apply the softmax-like distribution with the given base
        first_customers_sum = sum(y[:cutoff_idx])  # Sum of the first X% customers' assigned load
        # print(f"Base : {base},  First {target_customer_ratio*100:.1f}% of customers sum: {first_customers_sum}")
        return first_customers_sum - target_load_percentage  # Difference between actual and desired

    # Solve for the root using numerical optimization
    result = root_scalar(
        objective_function, method='brentq', bracket=[0.1, 20]  # Adjusted bracket range
    )

    # If root finding fails, fallback to a reasonable default
    return result.root if result.converged else 1


def load_distribution(num_customers,first_x_customer_percentage,load_percentage_for_first_x_percent_customers):
    # Example Parameters
    # num_customers = 10  # Total number of customers
    # first_x_customer_percentage = 20  # Percentage of customers considered (first 10%)
    # load_percentage_for_first_x_percent_customers = 90  # Percentage of load we want on the first X customers

    if math.floor(num_customers*first_x_customer_percentage/100)<1 :
        print("Input error: first_x_customer_percentage should cover alteast 1 customer")
        sys.exit()
    if first_x_customer_percentage>95:
        print("Customer percentage value is too high..")
        sys.exit()
    print(f"Finding optimal parameter to distribute {load_percentage_for_first_x_percent_customers}% assets to {first_x_customer_percentage}% of customers")
    # Dynamically compute optimal base for the desired parameters
    customer_ratio = first_x_customer_percentage/100
    optimal_exponent = find_optimal_exponent(num_customers,load_percentage_for_first_x_percent_customers,customer_ratio)
    # optimal_exponent = 1
    x = list(range(1, num_customers + 1))
    y = softmax(x, optimal_exponent)
    # print(y)
    print(f"Optimal Exponent Value to distribute assets in desired distribution is: {optimal_exponent}")
    print(f"First {customer_ratio*100:.1f}% of customers sum: {sum(y[:int(num_customers * customer_ratio)])}")
    # print(f"First value assigned: {y[0]}")
    return y

def adjust_allocation_to_match_total(current_segment_assets, initial_allocation):
    # Calculate the difference between the sum and total_assets
    difference = current_segment_assets - initial_allocation.sum()

    # Adjust the allocation
    if difference > 0:
        # Add 1 to some values to match the total
        for _ in range(difference):
            idx = np.argmin(initial_allocation)  # Add to the smallest values
            initial_allocation[idx] += 1
    elif difference < 0:
        # Subtract 1 from some values to match the total
        for _ in range(-difference):
            idx = np.argmax(initial_allocation)  # Subtract from the largest values
            initial_allocation[idx] -= 1

    # Ensure no value is zero
    initial_allocation[initial_allocation == 0] = 1

    # Final adjustment to maintain total assets
    while initial_allocation.sum() > current_segment_assets:
        idx = np.argmax(initial_allocation)
        initial_allocation[idx] -= 1

    return list(initial_allocation)

def return_asset_distribution(num_customers,first_x_customer_percentage,load_percentage_for_first_x_percent_customers,total_assets):

    y = load_distribution(num_customers,first_x_customer_percentage,load_percentage_for_first_x_percent_customers)
    initial_allocation = np.round(total_assets * np.array(y)/100).astype(int)
    cutoff_idx = math.floor(num_customers * first_x_customer_percentage/100)  # Cut-off index for the first X% customers

    print("Converting percentage values into actual assets count...")
    assets_to_enrol_for_each_customer_part1 = adjust_allocation_to_match_total(int(total_assets*load_percentage_for_first_x_percent_customers/100),initial_allocation[:cutoff_idx])
    assets_to_enrol_for_each_customer_part2 = adjust_allocation_to_match_total(int(total_assets*(100-load_percentage_for_first_x_percent_customers)/100),initial_allocation[cutoff_idx:])
    assets_to_enrol_for_each_customer = assets_to_enrol_for_each_customer_part1 + assets_to_enrol_for_each_customer_part2
    assets_to_enrol_for_each_customer = [int(value) for value in assets_to_enrol_for_each_customer]

    print("Total assets to allocate to all customers : ",sum(assets_to_enrol_for_each_customer))
    print("Total customers to allocate assets to : ",len(assets_to_enrol_for_each_customer))
    print("Asset distribution : ",assets_to_enrol_for_each_customer)
    print(f"First {first_x_customer_percentage:.1f}% of customers gets : {sum(assets_to_enrol_for_each_customer[:int(num_customers * first_x_customer_percentage/100)])} assets. ")
    print(f"And The last {100-first_x_customer_percentage:.1f}% of customers gets : {sum(assets_to_enrol_for_each_customer)- sum(assets_to_enrol_for_each_customer[:int(num_customers * first_x_customer_percentage/100)])} assets. ")
    return assets_to_enrol_for_each_customer