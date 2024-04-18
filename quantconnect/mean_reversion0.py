# region imports
from AlgorithmImports import *
# endregion

class EnergeticFluorescentOrangeShark(QCAlgorithm):

    def Initialize(self):
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2023, 12, 31)
        self.set_cash(100000)
    
        self.continuous_contract = self.add_future(
            Futures.Energies.CRUDE_OIL_WTI,
            data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
            data_mapping_mode=DataMappingMode.LAST_TRADING_DAY,
            contract_depth_offset=0,
            resolution=Resolution.MINUTE
        )

        self.window = 30
        self.long_entry = -2.0
        self.short_entry = 2.0
        self.long_exit = 0
        self.short_exit = 0

        # self.sma_fast = self.sma(self.continuous_contract.symbol, 5, Resolution.MINUTE)
        # self.sma_slow = self.sma(self.continuous_contract.symbol, 15, Resolution.MINUTE)

        self.moving_average = self.sma(self.continuous_contract.symbol, self.window, Resolution.MINUTE)
        self.standard_deviation = self.std(self.continuous_contract.symbol, self.window, Resolution.MINUTE)
        self.current_contract = None
        self.set_warm_up(self.window)

    def on_margin_call_warning(self):
        self.Error("You received a margin call warning")

    def on_order_event(self, order_event):
        self.debug(f"Open Position: {order_event.symbol} {order_event.direction} {order_event.fill_price}")

    def on_securities_changed(self, changes):
        self.debug(f"{self.time} -- {changes}")

    def compute_z_score(self):
        adjusted_price = self.securities[self.continuous_contract.symbol].price
        if self.standard_deviation.current.value == 0:
            z_score = 0
        else:
            z_score = (adjusted_price - self.moving_average.current.value) / self.standard_deviation.current.value

        return z_score

    def on_data(self, slice):
        if self.is_warming_up:
            return

        for changed_event in slice.SymbolChangedEvents.Values:
            if changed_event.Symbol == self.continuous_contract.Symbol:
                self.log(f"Symbol Changed event: {changed_event}")
        
        if not self.portfolio.invested:
            self.current_contract = self.securities[self.continuous_contract.mapped]
            if (self.time.hour == 10) and (self.time.minute > 25 and self.time.minute < 35) and (self.time.weekday() == 2):
                z_score = self.compute_z_score()
                if z_score < self.long_entry:
                    self.set_holdings(self.current_contract.symbol, 1)
                elif z_score > self.short_entry:
                    self.set_holdings(self.current_contract.symbol, -1)

        else:
            
            z_score = self.compute_z_score()
            if self.portfolio[self.current_contract.symbol].is_long:
                if z_score > self.long_exit:
                    self.liquidate()
            elif self.portfolio[self.current_contract.symbol].is_short:
                if z_score < self.short_exit:
                    self.liquidate()
            elif (self.time.hour == 12 and self.time.weekday() == 2):
                self.liquidate()

        # Checks if the current_contract is not the same as the contract currently mapped by the continuous future contract. 
        # If they are different, it means the continuous future contract has rolled over to a new contract. 
        # In this case, it logs the rollover event, liquidates the old contract, and goes long on the new contract with the same position size as before. 
        # The current_contract is then updated to the new contract.

        if self.current_contract is not None and self.current_contract.Symbol != self.continuous_contract.mapped:
            self.log(f"{time} - rolling position from {self.current_contract.symbol} to {self.continuous_contract.mapped}")
            current_position_size = self.current_contract.holdings.quantity
            self.liquidate(self.current_contract.Symbol)
            self.set_holdings(self.continuous_contract.mapped, current_position_size)
            self.current_contract = self.securities[self.continuous_contract.mapped]