from apps.activities.domain.conditions import (
    MultiSelectConditionType,
    SingleSelectConditionType,
)
from apps.activities.domain.response_type_config import ResponseType
from apps.activities.errors import (
    IncorrectConditionItemError,
    IncorrectConditionItemIndexError,
    IncorrectConditionLogicItemTypeError,
    IncorrectConditionOptionError,
    IncorrectScoreItemConfigError,
    IncorrectScoreItemError,
    IncorrectScoreItemTypeError,
    IncorrectScorePrintItemError,
    IncorrectScorePrintItemTypeError,
    IncorrectSectionConditionItemError,
    IncorrectSectionPrintItemError,
    IncorrectSectionPrintItemTypeError,
)


def validate_item_flow(values: dict):
    items = values.get("items", [])
    item_names = [item.name for item in items]

    # conditional logic for item flow
    for index in range(len(items)):
        if items[index].conditional_logic is not None:
            for condition in items[index].conditional_logic.conditions:
                # check if condition item name is in item names
                if condition.item_name not in item_names:
                    raise IncorrectConditionItemError()
                else:
                    # check if condition item order is less than current item order  # noqa: E501
                    condition_item_index = item_names.index(
                        condition.item_name
                    )
                    if condition_item_index > index:
                        raise IncorrectConditionItemIndexError()

                    # check if condition item type is correct
                    if items[condition_item_index].response_type not in [
                        ResponseType.SINGLESELECT,
                        ResponseType.MULTISELECT,
                        ResponseType.SLIDER,
                    ]:
                        raise IncorrectConditionLogicItemTypeError()

                    # check if condition option ids are correct
                    if condition.type in list(
                        SingleSelectConditionType
                    ) or condition.type in list(MultiSelectConditionType):
                        option_ids = [
                            option.id
                            for option in items[
                                condition_item_index
                            ].response_values.options
                        ]
                        if condition.payload.option_id not in option_ids:
                            raise IncorrectConditionOptionError()
    return values


def validate_score_and_sections(values: dict):
    items = values.get("items", [])
    item_names = [item.name for item in items]

    # conditional logic for scores and reports
    if hasattr(values, "scores_and_reports"):
        scores_and_reports: dict = values.scores_and_reports
        score_item_names = []
        score_condition_item_names = []
        # validate items in scores
        if hasattr(scores_and_reports, "scores"):
            for score in scores_and_reports.scores:
                score_item_names.append(score.name)
                # check if all item names are same as values.name
                for item in score.items_score:
                    if item not in item_names:
                        raise IncorrectScoreItemError()
                    else:
                        score_item_index = item_names.index(item)
                        if items[score_item_index].response_type not in [
                            ResponseType.SINGLESELECT,
                            ResponseType.MULTISELECT,
                            ResponseType.SLIDER,
                        ]:
                            raise IncorrectScoreItemTypeError()
                        if not items[score_item_index].config.add_scores:
                            raise IncorrectScoreItemConfigError()

                for item in score.items_print:
                    if item not in item_names:
                        raise IncorrectScorePrintItemError()
                    else:
                        if items[item_names.index(item)].response_type not in [
                            ResponseType.SINGLESELECT,
                            ResponseType.MULTISELECT,
                            ResponseType.SLIDER,
                            ResponseType.TEXT,
                        ]:
                            raise IncorrectScorePrintItemTypeError()

                if score.get("conditional_logic"):
                    for conditional_logic in score.conditional_logic:
                        score_condition_item_names.append(
                            conditional_logic.name
                        )
                        for item in conditional_logic.items_print:
                            if item not in item_names:
                                raise IncorrectScorePrintItemError()
                            else:
                                if items[
                                    item_names.index(item)
                                ].response_type not in [
                                    ResponseType.SINGLESELECT,
                                    ResponseType.MULTISELECT,
                                    ResponseType.SLIDER,
                                    ResponseType.TEXT,
                                ]:
                                    raise IncorrectScorePrintItemTypeError()

        # validate items in sections
        if hasattr(scores_and_reports, "sections"):
            for section in scores_and_reports.sections:
                for item in section.items_print:
                    if item not in item_names:
                        raise IncorrectSectionPrintItemError()
                    else:
                        if items[item_names.index(item)].response_type not in [
                            ResponseType.SINGLESELECT,
                            ResponseType.MULTISELECT,
                            ResponseType.SLIDER,
                            ResponseType.TEXT,
                        ]:
                            raise IncorrectSectionPrintItemTypeError()

                if section.get("conditional_logic"):
                    for item in section.conditional_logic.items_print:
                        if item not in item_names:
                            raise IncorrectSectionPrintItemError()
                        else:
                            if items[
                                item_names.index(item)
                            ].response_type not in [
                                ResponseType.SINGLESELECT,
                                ResponseType.MULTISELECT,
                                ResponseType.SLIDER,
                                ResponseType.TEXT,
                            ]:
                                raise IncorrectSectionPrintItemTypeError()
                    for item in section.conditional_logic.conditions:
                        if (
                            item.item_name not in item_names
                            or item.item_name not in score_item_names
                            or item.item_name not in score_condition_item_names
                        ):
                            raise IncorrectSectionConditionItemError()

    return values