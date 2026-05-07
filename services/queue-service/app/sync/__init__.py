"""Cross-service synchronization consumers.

Each consumer here subscribes to RabbitMQ events that other services publish
and reconciles state inside its own database. This is how services with
private DBs stay coherent without sharing tables or doing cross-DB joins.
"""
