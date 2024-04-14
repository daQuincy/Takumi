from clr import AddReference
AddReference("System")
AddReference("QuantConnect.Algorithm")
AddReference("QuantConnect.Common")

from AlgorithmImports import *
from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Indicators import *
from scipy.stats import zscore

import math

class FuturesBuyAndHold(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2023, 6, 1)
        self.SetEndDate(2023, 10, 31)
        self.SetCash(100000)
    
        self.future = self.AddFuture(Futures.Energies.CRUDE_OIL_WTI)
        self.future.SetFilter(0, 90)

        # widen the free portfolio percentage to 30% to avoid margin calls for futures
        self.Settings.FreePortfolioValuePercentage = 0.3

    def OnMarginCallWarning(self):
        self.Error("You received a margin call warning")


    def OnData(self, slice):
        # loop over each available future chains from slice
        for chain in slice.FutureChains:
            # filter to choose contract with OpenInterest > 1000
            self.popular_contracts = [contract for contract in chain.Value if contract.OpenInterest > 1000]
            if len(self.popular_contracts) == 0:
                continue

            sortedByOIContracts = sorted(self.popular_contracts, key=lambda k: k.OpenInterest, reverse=True) 
            self.liquidContract = sortedByOIContracts[0]

            if not self.Portfolio.Invested:
                # self.notionalValue = self.liquidContract.AskPrice * self.future.SymbolProperties.ContractMultiplier
                # future = self.Securities[self.liquidContract.Symbol]

                # # calculate number of contracts we can afford based on required margin
                # margin_remaining = self.Portfolio.MarginRemaining
                # initial_margin = future.BuyingPowerModel.InitialOvernightMarginRequirement
                # self.contractsToBuy = math.floor(margin_remaining / initial_margin)

                # self.MarketOrder(self.liquidContract.Symbol, self.contractsToBuy)
                self.SetHoldings(self.liquidContract.Symbol, 1)