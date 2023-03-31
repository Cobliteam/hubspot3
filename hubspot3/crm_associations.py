"""
hubspot crm_associations api
"""
import itertools
from enum import Enum
from typing import Iterator

from hubspot3.base import BaseClient
from hubspot3.lines import LinesClient
from hubspot3.tickets import TicketsClient
from hubspot3.utils import get_log

ASSOCIATIONS_API_VERSION = "3"


class Definitions(Enum):
    """
    :see: https://developers.hubspot.com/docs/methods/crm-associations/crm-associations-overview
    """

    CONTACT_TO_COMPANY = 1
    COMPANY_TO_CONTACT = 2
    DEAL_TO_CONTACT = 3
    CONTACT_TO_DEAL = 4
    DEAL_TO_COMPANY = 5
    COMPANY_TO_DEAL = 6
    COMPANY_TO_ENGAGEMENT = 7
    ENGAGEMENT_TO_COMPANY = 8
    CONTACT_TO_ENGAGEMENT = 9
    ENGAGEMENT_TO_CONTACT = 10
    DEAL_TO_ENGAGEMENT = 11
    ENGAGEMENT_TO_DEAL = 12
    PARENT_COMPANY_TO_CHILD_COMPANY = 13
    CHILD_COMPANY_TO_PARENT_COMPANY = 14
    CONTACT_TO_TICKET = 15
    TICKET_TO_CONTACT = 16
    TICKET_TO_ENGAGEMENT = 17
    ENGAGEMENT_TO_TICKET = 18
    DEAL_TO_LINE_ITEM = 19
    LINE_ITEM_TO_DEAL = 20
    COMPANY_TO_TICKET = 25
    TICKET_TO_COMPANY = 26
    DEAL_TO_TICKET = 27
    TICKET_TO_DEAL = 28
    OWNER_TO_COMPANY = 41


class CRMAssociationsClient(BaseClient):
    """
    Associations extension for Associations API endpoint
    :see: https://developers.hubspot.com/docs/methods/crm-associations/crm-associations-overview
    """

    def __init__(self, *args, **kwargs):
        super(CRMAssociationsClient, self).__init__(*args, **kwargs)
        self.log = get_log("hubspot3.crm_associations")

    def _get_path(self, subpath):
        return "crm/v{}/{}".format(
            self.options.get("version") or ASSOCIATIONS_API_VERSION, subpath
        )

    def get(self, object_id, definition: Definitions):
        """
        get all associations for the defined object
        :param object_id: Object ID for the object you're looking up
        :param definition: Definition ID for the objects you're looking for associations of
        """
        finished = False
        output = []
        offset = 0
        query_limit = 100  # Max value according to docs

        while not finished:
            batch = self._call(
                "associations/{}/{}/{}".format(
                    object_id, "HUBSPOT_DEFINED", definition.value
                ),
                method="GET",
                params={"limit": query_limit, "offset": offset},
            )
            output.extend([id_ for id_ in batch["results"]])
            finished = not batch["hasMore"]
            offset = batch["offset"]

        return output

    def get_all(self, object_id, definition: Definitions, **options):
        """
        get all crm associations
        :param object_id: Object ID for the object you're looking up
        :param definition: Definition ID for the objects you're looking for associations of
        """
        finished = False
        output = []
        offset = 0
        query_limit = 100  # Max value according to docs

        while not finished:
            batch = self._call(
                "associations/{}/{}/{}".format(
                    object_id, "HUBSPOT_DEFINED", definition.value
                ),
                method="GET",
                params={"limit": query_limit, "offset": offset},
            )
            output.extend([id_ for id_ in batch["results"]])
            finished = not batch["hasMore"]
            offset = batch["offset"]

        return output

    def create(self, from_object, to_object, definition: Definitions, **options):
        """
        create a hubspot association
        :param from_object: ID of object to relate
        :param to_object: ID of object to relate to
        :param definition: Definition ID for the objects you're looking for associations of
        """
        return self._call(
            "associations",
            method="PUT",
            data={
                "fromObjectId": from_object,
                "toObjectId": to_object,
                "category": "HUBSPOT_DEFINED",
                "definitionId": definition.value,
            },
            **options
        )

    def delete(self, from_object, to_object, definition: Definitions, **options):
        """
        delete a hubspot association
        :param from_object: ID of object to relate
        :param to_object: ID of object to relate to
        :param definition: Definition ID for the objects you're looking for associations of
        """
        return self._call(
            "associations/delete",
            method="PUT",
            data={
                "fromObjectId": from_object,
                "toObjectId": to_object,
                "category": "HUBSPOT_DEFINED",
                "definitionId": definition.value,
            },
            **options
        )

    def get_deal_to_lines_items(self, deal_id):
        """Get the lines related to a deal."""
        return self.get(object_id=deal_id, definition=Definitions.DEAL_TO_LINE_ITEM)

    def get_company_to_contacts(self, company_id):
        """Get the contacts related to a company."""
        return self.get(object_id=company_id, definition=Definitions.COMPANY_TO_CONTACT)

    def get_company_to_deals(self, company_id):
        """Get the deals related to a company."""
        return self.get(object_id=company_id, definition=Definitions.COMPANY_TO_DEAL)

    def link_line_item_to_deal(self, line_item_id, deal_id):
        """Create a new association between a line item and a deal."""
        return self.create(
            from_object=line_item_id,
            to_object=deal_id,
            definition=Definitions.LINE_ITEM_TO_DEAL,
        )

    def link_contact_to_company(self, contact_id, company_id):
        """Create a new association between a contact and a company."""
        return self.create(
            from_object=contact_id,
            to_object=company_id,
            definition=Definitions.CONTACT_TO_COMPANY,
        )

    def link_owner_to_company(self, owner_id, company_id):
        """Create a new association between an owner and a company."""
        return self.create(
            from_object=owner_id,
            to_object=company_id,
            definition=Definitions.OWNER_TO_COMPANY,
        )

    def chunks(self, iterable, size=100):
        length = len(iterable)
        it = iter(iterable)
        for i in range(0, int(length / size) + (length % size > 0)):
            r = []
            for item in itertools.islice(it, size):
                r.append(item)
            yield r

    def get_all_as_generator(
        self,
        fromObjectType: str,
        toObjectType: str,
        listObjects: Iterator[dict],
        limit: int = -1,
    ) -> Iterator[dict]:
        """
        get all associations batch
        :see: https://developers.hubspot.com/docs/api/crm/associations/v3
        """
        limited = limit > 0

        offset = 0
        total = 0
        outputs = []
        index = 0
        for list_obj in self.chunks(listObjects, 150):
            index = index + 1
            dict_obj = dict()
            dict_obj["inputs"] = list_obj
            batch = self._call(
                "associations/{}/{}/batch/read".format(fromObjectType, toObjectType),
                method="POST",
                doseq=True,
                params={"offset": offset},
                data=dict_obj,
            )
            outputs.extend(batch["results"])

        total = len(outputs)

        reached_limit = limited and total >= limit

        # Since the API doesn't aways tries to return 100 line items we may pass the desired limit
        if reached_limit:
            outputs = outputs[:limit]

        yield from outputs

    def get_lines_items_to_deals(self) -> list:
        """Get the lines related to a deal."""
        lines_client = LinesClient(**self.credentials)
        generator = self.get_all_as_generator(
            fromObjectType="line_items",
            toObjectType="deals",
            listObjects=lines_client.get_all_ids(),
        )
        return list(generator)

    def get_tickets_to_engagements(self) -> list:
        """From a ticket, get associated engagement to it"""
        ticket_client = TicketsClient(**self.credentials)
        generator = self.get_all_as_generator(
            fromObjectType="tickets",
            toObjectType="engagements",
            listObjects=ticket_client.get_all(),
        )
        return list(generator)
