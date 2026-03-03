from unittest.mock import patch

from orders.enums import OrderStatus


class TestOrderDeliveredStockSignal:
    def test_signal_enqueues_on_delivered(self, order_factory):
        with patch("stock.tasks.debit_stock_for_order.delay") as mock_delay:
            order = order_factory(status=OrderStatus.PENDING)
            order.status = OrderStatus.DELIVERED
            order.save()

            mock_delay.assert_called_once_with(str(order.id))

    def test_signal_ignores_non_delivered(self, order_factory):
        with patch("stock.tasks.debit_stock_for_order.delay") as mock_delay:
            order = order_factory(status=OrderStatus.PENDING)
            order.status = OrderStatus.CONFIRMED
            order.save()

            mock_delay.assert_not_called()

    def test_signal_ignores_pending(self, order_factory):
        with patch("stock.tasks.debit_stock_for_order.delay") as mock_delay:
            order_factory(status=OrderStatus.PENDING)
            # Only 1 call during creation (PENDING), signal should not trigger debit
            mock_delay.assert_not_called()
