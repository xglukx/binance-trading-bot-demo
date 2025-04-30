# Demo Cryptocurrency Trading Bot: Showcase of Coding Capabilities

## IMPORTANT NOTICE

**This is a DEMO project created solely to showcase coding capabilities. It is NOT intended for actual trading use and should NOT be reused in production environments.**

This repository contains intentionally simplified and modified code that demonstrates coding patterns and architecture, but does not contain any actual trading strategies or sensitive information.

## Project Overview

This demo trading bot is a showcase of an architecture for a cryptocurrency exchange WebSocket client that could, in theory, leverage technical indicators to process market data. The real implementation would require significant enhancements, proper testing, and risk management features before being suitable for actual trading.

## Demonstrated Technical Concepts

* **WebSocket Connectivity** - Handling real-time data streams from cryptocurrency exchanges
* **Technical Indicators** - Implementation of common technical analysis indicators
* **Event-Driven Architecture** - Using callbacks and subscriptions for real-time processing
* **Error Handling** - Comprehensive error catching and logging
* **Reconnection Logic** - Automatic handling of connection failures with exponential backoff
* **Containerization** - Docker setup for consistent deployment

## Technical Architecture

The demo bot showcases a modern technology stack:

* **Python 3.9** with asynchronous processing for efficient data handling
* **Docker** containerization for consistent deployment
* **Pandas/NumPy** for numerical operations and technical analysis
* **WebSocket** communication for real-time market data

## Code Organization

* **ws_indicators.py** - Technical indicators calculator
* **exchange_ws_client.py** - WebSocket client for exchange communication
* **Docker configuration** - Containerization setup
* **Shell scripts** - Deployment and setup automation

## Development Approaches Demonstrated

This project showcases several modern development approaches:

1. **Modular Architecture** - Separation of concerns between data collection and analysis
2. **Asynchronous Processing** - Handling real-time data streams efficiently
3. **Error Resilience** - Comprehensive error handling and recovery mechanisms
4. **Configuration Management** - Using environment variables for flexible configuration

## Disclaimer

This code is provided for demonstration purposes only. It:

* Contains intentionally modified algorithms
* Does not implement any real trading strategies
* Replaces actual exchange-specific code with generic implementations
* Should not be used as the basis for actual trading systems without substantial enhancements

**The author assumes no responsibility for any use of this code in actual trading or financial scenarios.**

---

*This project demonstrates technical capabilities in building complex, real-time data processing systems, but is NOT a functional trading system.* 