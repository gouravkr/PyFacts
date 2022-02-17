# Fincal
This module simplified handling of time-series data

## The problem
Time series data often have missing data points. These missing points mess things up when you are trying to do a comparison between two sections of a time series.

To make things worse, most libraries don't allow comparison based on dates. Month to Month and year to year comparisons become difficult as they cannot be translated into number of days. However, these are commonly used metrics while looking at financial data.

## The Solution
Fincal aims to simplify things by allowing you to:
* Compare time-series data based on dates
* Easy way to work around missing dates by taking the closest data points
* Completing series with missing data points using forward fill and backward fill

## Examples