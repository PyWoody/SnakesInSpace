from datetime import datetime, timezone


class SpaceBaseException(Exception):
    pass


class ClientError(SpaceBaseException):

    def __init__(self, msg=None, data=None):
        msg = msg if msg is not None else 'Generic Client Exception'
        super().__init__(msg)
        self.data = data
        self.__raised_at = datetime.now(timezone.utc)

    @property
    def raised_at(self):
        return self.__raised_at


class SpaceAttributeError(SpaceBaseException):
    pass


class SpaceUserError(SpaceBaseException):
    pass


class NoShipAtLocationError(SpaceBaseException):
    pass


# General Error Codes
class CooldownConflictError(SpaceBaseException):
    error_code = 4000


class WaypointNoAccessError(SpaceBaseException):
    error_code = 4001


# Account Error Codes
class AccountException(SpaceBaseException):
    pass


class TokenEmptyError(AccountException):
    error_code = 4100


class TokenMissingSubjectError(AccountException):
    error_code = 4101


class TokenInvalidSubjectError(AccountException):
    error_code = 4102


class MissingTokenRequestError(AccountException):
    error_code = 4103


class InvalidTokenRequestError(AccountException):
    error_code = 4104


class InvalidTokenSubjectError(AccountException):
    error_code = 4105


class AccountNotExistsError(AccountException):
    error_code = 4106


class AgentNotExistsError(AccountException):
    error_code = 4107


class AccountHasNoAgentError(AccountException):
    error_code = 4108


class RegisterAgentExistsError(AccountException):
    error_code = 4109


class RegisterAgentSymbolReservedError(AccountException):
    error_code = 4110


class RegisterAgentConflictSymbolError(AccountException):
    error_code = 4111


# Ship Error Codes
class ShipException(SpaceBaseException):
    pass


class NavigateInTransitError(ShipException):
    error_code = 4200


class NavigateInvalidDestinationError(ShipException):
    error_code = 4201


class NavigateOutsideSystemError(ShipException):
    error_code = 4202


class NavigateInsufficientFuelError(ShipException):
    error_code = 4203


class NavigateSameDestinationError(ShipException):
    error_code = 4204


class ShipExtractInvalidWaypointError(ShipException):
    error_code = 4205


class ShipExtractPermissionError(ShipException):
    error_code = 4206


class ShipJumpNoSystemError(ShipException):
    error_code = 4207


class ShipJumpSameSystemError(ShipException):
    error_code = 4208


class ShipJumpMissingModuleError(ShipException):
    error_code = 4210


class ShipJumpNoValidWaypointError(ShipException):
    error_code = 4211


class ShipJumpMissingAntimatterError(ShipException):
    error_code = 4212


class ShipInTransitError(ShipException):
    error_code = 4214


class ShipMissingSensorArraysError(ShipException):
    error_code = 4215


class PurchaseShipCreditsError(ShipException):
    error_code = 4216


class ShipCargoExceedsLimitError(ShipException):
    error_code = 4217


class ShipCargoMissingError(ShipException):
    error_code = 4218


class ShipCargoUnitCountError(ShipException):
    error_code = 4219


class ShipSurveyVerificationError(ShipException):
    error_code = 4220


class ShipSurveyExpirationError(ShipException):
    error_code = 4221


class ShipSurveyWaypointTypeError(ShipException):
    error_code = 4222


class ShipSurveyOrbitError(ShipException):
    error_code = 4223


class ShipSurveyExhaustedError(ShipException):
    error_code = 4224


class ShipRefuelDockedError(ShipException):
    error_code = 4225


class ShipRefuelInvalidWaypointError(ShipException):
    error_code = 4226


class ShipCargoFullError(ShipException):
    error_code = 4228


class ShipJumpFromGateToGateError(ShipException):
    error_code = 4229


class WaypointChartedError(ShipException):
    error_code = 4230


class ShipTransferShipNotFound(ShipException):
    error_code = 4231


class ShipTransferAgentConflict(ShipException):
    error_code = 4232


class ShipTransferSameShipConflict(ShipException):
    error_code = 4233


class ShipTransferLocationConflict(ShipException):
    error_code = 4234


class WarpInsideSystemError(ShipException):
    error_code = 4235


class ShipNotInOrbitError(ShipException):
    error_code = 4236


class ShipInvalidRefineryGoodError(ShipException):
    error_code = 4237


class ShipInvalidRefineryTypeError(ShipException):
    error_code = 4238


class ShipMissingRefineryError(ShipException):
    error_code = 4239


class ShipMissingSurveyorError(ShipException):
    error_code = 4240


class ShipMissingWarpDriveError(ShipException):
    error_code = 4241


class ShipMissingMineralProcessorError(ShipException):
    error_code = 4242


class ShipMissingMiningLasersError(ShipException):
    error_code = 4243


class ShipNotDockedError(ShipException):
    error_code = 4244


class PurchaseShipNotPresentError(ShipException):
    error_code = 4245


class ShipMountNoShipyardError(ShipException):
    error_code = 4246


class ShipMissingMountError(ShipException):
    error_code = 4247


class ShipMountInsufficientCreditsError(ShipException):
    error_code = 4248


class ShipMissingPowerError(ShipException):
    error_code = 4249


class ShipMissingSlotsError(ShipException):
    error_code = 4250


class ShipMissingMountsError(ShipException):
    error_code = [4251, 4227]


class ShipMissingCrewError(ShipException):
    error_code = 4252


class ShipExtractDestabilizedError(ShipException):
    error_code = 4253


class ShipJumpInvalidOriginError(ShipException):
    error_code = 4254


class ShipJumpInvalidWaypointError(ShipException):
    error_code = 4255


class ShipJumpOriginUnderConstructionError(ShipException):
    error_code = 4256


class ShipMissingGasProcessorError(ShipException):
    error_code = 4257


class ShipMissingGasSiphonsError(ShipException):
    error_code = 4258


class ShipSiphonInvalidWaypointError(ShipException):
    error_code = 4259


class ShipSiphonPermissionError(ShipException):
    error_code = 4260


class WaypointNoYieldError(ShipException):
    error_code = 4261


class ShipJumpDestinationUnderConstructionError(ShipException):
    error_code = 4262


# Contract Error Codes
class ContractException(SpaceBaseException):
    pass


class AcceptContractNotAuthorizedError(ContractException):
    error_code = 4500


class AcceptContractConflictError(ContractException):
    error_code = 4501


class FulfillContractDeliveryError(ContractException):
    error_code = 4502


class ContractDeadlineError(ContractException):
    error_code = 4503


class ContractFulfilledError(ContractException):
    error_code = 4504


class ContractNotAcceptedError(ContractException):
    error_code = 4505


class ContractNotAuthorizedError(ContractException):
    error_code = 4506


class ShipDeliverTermsError(ContractException):
    error_code = 4508


class ShipDeliverFulfilledError(ContractException):
    error_code = 4509


class ShipDeliverInvalidLocationError(ContractException):
    error_code = 4510


class ExistingContractError(ContractException):
    error_code = 4511


# Market Error Codes
class MarketException(SpaceBaseException):
    pass


class MarketInsufficientCredits(MarketException):
    error_code = 4600


class MarketTradeNoPurchaseError(MarketException):
    error_code = 4601


class MarketTradeNotSoldError(MarketException):
    error_code = 4602


class MarketNotFoundError(MarketException):
    error_code = 4603


class MarketTradeUnitLimitError(MarketException):
    error_code = 4604


# Faction Error Codes
class FactionException(SpaceBaseException):
    pass


class WaypointNoFactionError(FactionException):
    error_code = 4700


# Construction Error Code
class ConstructionException(SpaceBaseException):
    pass


class ConstructionMaterialNotRequired(ConstructionException):
    error_code = 4800


class ConstructionMaterialFulfilled(ConstructionException):
    error_code = 4801


class ShipConstructionInvalidLocationError(ConstructionException):
    error_code = 4802


error_codes = {
    # TODO: hiearchy
    # General Error Codes
    4000: CooldownConflictError,
    4001: WaypointNoAccessError,

    # Account Error Codes
    4100: TokenEmptyError,
    4101: TokenMissingSubjectError,
    4102: TokenInvalidSubjectError,
    4103: MissingTokenRequestError,
    4104: InvalidTokenRequestError,
    4105: InvalidTokenSubjectError,
    4106: AccountNotExistsError,
    4107: AgentNotExistsError,
    4108: AccountHasNoAgentError,
    4109: RegisterAgentExistsError,
    4110: RegisterAgentSymbolReservedError,
    4111: RegisterAgentConflictSymbolError,

    # Ship Error Codes
    4200: NavigateInTransitError,
    4201: NavigateInvalidDestinationError,
    4202: NavigateOutsideSystemError,
    4203: NavigateInsufficientFuelError,
    4204: NavigateSameDestinationError,
    4205: ShipExtractInvalidWaypointError,
    4206: ShipExtractPermissionError,
    4207: ShipJumpNoSystemError,
    4208: ShipJumpSameSystemError,
    4210: ShipJumpMissingModuleError,
    4211: ShipJumpNoValidWaypointError,
    4212: ShipJumpMissingAntimatterError,
    4214: ShipInTransitError,
    4215: ShipMissingSensorArraysError,
    4216: PurchaseShipCreditsError,
    4217: ShipCargoExceedsLimitError,
    4218: ShipCargoMissingError,
    4219: ShipCargoUnitCountError,
    4220: ShipSurveyVerificationError,
    4221: ShipSurveyExpirationError,
    4222: ShipSurveyWaypointTypeError,
    4223: ShipSurveyOrbitError,
    4224: ShipSurveyExhaustedError,
    4225: ShipRefuelDockedError,
    4226: ShipRefuelInvalidWaypointError,
    4227: ShipMissingMountsError,  # Just a guess. It's a duplicate
    4228: ShipCargoFullError,
    4229: ShipJumpFromGateToGateError,
    4230: WaypointChartedError,
    4231: ShipTransferShipNotFound,
    4232: ShipTransferAgentConflict,
    4233: ShipTransferSameShipConflict,
    4234: ShipTransferLocationConflict,
    4235: WarpInsideSystemError,
    4236: ShipNotInOrbitError,
    4237: ShipInvalidRefineryGoodError,
    4238: ShipInvalidRefineryTypeError,
    4239: ShipMissingRefineryError,
    4240: ShipMissingSurveyorError,
    4241: ShipMissingWarpDriveError,
    4242: ShipMissingMineralProcessorError,
    4243: ShipMissingMiningLasersError,
    4244: ShipNotDockedError,
    4245: PurchaseShipNotPresentError,
    4246: ShipMountNoShipyardError,
    4247: ShipMissingMountError,
    4248: ShipMountInsufficientCreditsError,
    4249: ShipMissingPowerError,
    4250: ShipMissingSlotsError,
    4251: ShipMissingMountsError,
    4252: ShipMissingCrewError,
    4253: ShipExtractDestabilizedError,
    4254: ShipJumpInvalidOriginError,
    4255: ShipJumpInvalidWaypointError,
    4256: ShipJumpOriginUnderConstructionError,
    4257: ShipMissingGasProcessorError,
    4258: ShipMissingGasSiphonsError,
    4259: ShipSiphonInvalidWaypointError,
    4260: ShipSiphonPermissionError,
    4261: WaypointNoYieldError,
    4262: ShipJumpDestinationUnderConstructionError,

    # Contract Error Codes
    4500: AcceptContractNotAuthorizedError,
    4501: AcceptContractConflictError,
    4502: FulfillContractDeliveryError,
    4503: ContractDeadlineError,
    4504: ContractFulfilledError,
    4505: ContractNotAcceptedError,
    4506: ContractNotAuthorizedError,
    4508: ShipDeliverTermsError,
    4509: ShipDeliverFulfilledError,
    4510: ShipDeliverInvalidLocationError,
    4511: ExistingContractError,

    # Market Error Codes
    4600: MarketInsufficientCredits,
    4601: MarketTradeNoPurchaseError,
    4602: MarketTradeNotSoldError,
    4603: MarketNotFoundError,
    4604: MarketTradeUnitLimitError,

    # Faction Error Codes
    4700: WaypointNoFactionError,

    # Construction Error Code
    4800: ConstructionMaterialNotRequired,
    4801: ConstructionMaterialFulfilled,
    4802: ShipConstructionInvalidLocationError,
}
