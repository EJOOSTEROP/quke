"""
rate_limiter.py

This module manages rate limiters for limiting the rate of operations, particularly useful for
controlling the rate of requests to APIs or other rate-sensitive systems.

It uses an in-memory rate limiter implementation provided by the `langchain_core.rate_limiters` 
module. The rate limiters are stored in a global dictionary and can be retrieved or created 
using their names.

Functions:
- create_rate_limiter(name: str, **kwargs): Creates a new rate limiter and adds it to the global 
  dictionary if it does not already exist.
- get_rate_limiter(name: str, **kwargs) -> InMemoryRateLimiter: Retrieves a rate limiter by name 
  from the global dictionary. If it does not exist, it creates a new one using the provided 
  parameters.

Example usage:
    if __name__ == "__main__":
        # Create or get a rate limiter named 'api_limiter' with a limit of 5 requests per second
        limiter = get_rate_limiter("api_limiter", requests_per_second=5)
        print(limiter)

Global Variables:
- rate_limiters (Dict[str, InMemoryRateLimiter]): A global dictionary that stores rate limiters 
  by their names.

Dependencies:
- langchain_core.rate_limiters.InMemoryRateLimiter: The in-memory rate limiter class used to 
  instantiate rate limiters.

This module is designed to be flexible and can be extended or modified to support additional 
features or different types of rate limiters as needed.
"""

import logging  # functionality managed by Hydra
from typing import Dict

from langchain_core.rate_limiters import InMemoryRateLimiter

# Global dictionary to store rate limiters by name
rate_limiters: Dict[str, InMemoryRateLimiter] = {}


def create_rate_limiter(name: str, **kwargs):
    """
    Create a new rate limiter and add it to the global dictionary.

    If a limiter already exists with the same name, it will not be added.

    Parameters:
    - name (str): The name to key the rate limiter in the global dictionary.
    - **kwargs: Arbitrary keyword arguments to pass to the InMemoryRateLimiter constructor.

    Returns:
    - None
    """
    # Check if the name is already in the global dictionary
    if name in rate_limiters:
        return

    rate_limiter = InMemoryRateLimiter(**kwargs)

    # Add the new rate limiter to the global dictionary
    rate_limiters[name] = rate_limiter

    logging.info(f"Rate limiter '{name}' created with parameters: {kwargs}.")


def get_rate_limiter(name: str, **kwargs) -> InMemoryRateLimiter:
    """
    Retrieve an InMemoryRateLimiter from the global dictionary by name. If it does not
    exist, create it using the create_rate_limiter function.

    Parameters:
    - name (str): The name to key the rate limiter in the global dictionary.
    - **kwargs: Arbitrary keyword arguments to pass to the InMemoryRateLimiter constructor.

    Returns:
    - InMemoryRateLimiter: The retrieved or newly created rate limiter.
    """
    if name not in rate_limiters:
        create_rate_limiter(name, **kwargs)

    logging.info("Using rate limiter: " + name)
    return rate_limiters[name]
