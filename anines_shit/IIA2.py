def calculate_Q(m, n, k):
    """
    Calculate the Q factor as per given formula: Q = min(1, m*n/k)

    Parameters:
    - m, n, k: parameters related to bandwidth.

    Returns:
    float: Q factor
    """
    return min(1, m * n / k)


def calculate_MOS(Q):
    """
    Calculate the MOS score based on the Q factor using the given step function.

    Parameters:
    - Q: quality factor

    Returns:
    int: MOS score (1-5)
    """
    # Threshold values
    q = [0.0, 0.5, 0.6, 0.8, 0.9, 1.0]

    # Define MOS score
    for i in range(1, 6):
        if q[i - 1] < Q <= q[i]:
            return i

    # Default MOS score if Q does not match any condition
    # (not needed if Q is always within the predefined thresholds)
    return 1


# Example usage:
# m, n, k are bandwidth-related variables and should be defined
m = 10
n = 2
k = 25

# Calculate Q
Q = calculate_Q(m, n, k)

# Calculate MOS
mos_score = calculate_MOS(Q)

print(f"Q: {Q}, MOS Score: {mos_score}")
