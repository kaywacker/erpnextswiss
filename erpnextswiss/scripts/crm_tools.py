# -*- coding: utf-8 -*-
#
# crm_tools.py
#
# Copyright (C) libracore, 2017-2024
# https://www.libracore.com or https://github.com/libracore
#

import frappe


def _get_first_link(link_doctype, link_name, parenttype):
    rows = frappe.db.sql(
        """SELECT `parent` FROM `tabDynamic Link`
            WHERE `link_doctype` = %s
              AND `link_name` = %s
              AND `parenttype` = %s""",
        (link_doctype, link_name, parenttype),
        as_dict=True,
    )
    return rows[0]["parent"] if rows else None


def _get_primary_link(link_doctype, link_name, parenttype, primary_field):
    join_table = "tabAddress" if parenttype == "Address" else "tabContact"
    rows = frappe.db.sql(
        """SELECT `tabDynamic Link`.`parent`, `{join_table}`.`{primary_field}`
            FROM `tabDynamic Link`
            LEFT JOIN `{join_table}` ON `{join_table}`.`name` = `tabDynamic Link`.`parent`
            WHERE `tabDynamic Link`.`link_doctype` = %s
              AND `tabDynamic Link`.`link_name` = %s
              AND `tabDynamic Link`.`parenttype` = %s
            ORDER BY `{join_table}`.`{primary_field}` DESC""".format(
            join_table=join_table, primary_field=primary_field
        ),
        (link_doctype, link_name, parenttype),
        as_dict=True,
    )
    return rows[0]["parent"] if rows else None


# fetch the first available address from a customer
@frappe.whitelist()
def get_customer_address(customer):
    frappe.has_permission("Customer", "read", customer, throw=True)
    name = _get_first_link("Customer", customer, "Address")
    return frappe.get_doc("Address", name) if name else None


# fetch the primary available address from a customer
@frappe.whitelist()
def get_primary_customer_address(customer):
    frappe.has_permission("Customer", "read", customer, throw=True)
    name = _get_primary_link("Customer", customer, "Address", "is_primary_address")
    return frappe.get_doc("Address", name) if name else None


# fetch the primary available contact from a customer
@frappe.whitelist()
def get_primary_customer_contact(customer):
    frappe.has_permission("Customer", "read", customer, throw=True)
    name = _get_primary_link("Customer", customer, "Contact", "is_primary_contact")
    return frappe.get_doc("Contact", name) if name else None


# fetch the first available contact from a customer
@frappe.whitelist()
def get_customer_contact(customer):
    frappe.has_permission("Customer", "read", customer, throw=True)
    name = _get_first_link("Customer", customer, "Contact")
    return frappe.get_doc("Contact", name) if name else None


# fetch the first available address from a supplier
@frappe.whitelist()
def get_supplier_address(supplier):
    frappe.has_permission("Supplier", "read", supplier, throw=True)
    name = _get_first_link("Supplier", supplier, "Address")
    return frappe.get_doc("Address", name) if name else None


# fetch the primary available address from a supplier
@frappe.whitelist()
def get_primary_supplier_address(supplier):
    frappe.has_permission("Supplier", "read", supplier, throw=True)
    name = _get_primary_link("Supplier", supplier, "Address", "is_primary_address")
    return frappe.get_doc("Address", name) if name else None


# fetch the primary available contact from a supplier
@frappe.whitelist()
def get_primary_supplier_contact(supplier):
    frappe.has_permission("Supplier", "read", supplier, throw=True)
    name = _get_primary_link("Supplier", supplier, "Contact", "is_primary_contact")
    return frappe.get_doc("Contact", name) if name else None


# fetch the primary available address from a company
@frappe.whitelist()
def get_primary_company_address(company):
    frappe.has_permission("Company", "read", company, throw=True)
    name = _get_primary_link("Company", company, "Address", "is_primary_address")
    return frappe.get_doc("Address", name) if name else None


@frappe.whitelist()
def update_contact_first_and_last_name(contact, firstname, lastname):
    frappe.has_permission("Contact", "write", contact, throw=True)
    contact = frappe.get_doc("Contact", contact)
    contact.first_name = firstname
    contact.last_name = lastname
    contact.save()


# Whitelist of doctypes accepted by change_customer_without_impact_on_price.
# Used to validate the table-name interpolation; without this gate any
# authenticated user could write to any tab*.
_ALLOWED_SALES_DT = {"Quotation", "Sales Order", "Sales Invoice", "Delivery Note"}


@frappe.whitelist()
def change_customer_without_impact_on_price(dt, record, customer, address=None, contact=None):
    if dt not in _ALLOWED_SALES_DT:
        frappe.throw("Unsupported doctype: {0}".format(frappe.utils.cstr(dt)))
    if not frappe.db.exists(dt, record):
        frappe.throw("{0} {1} not found".format(dt, frappe.utils.cstr(record)))
    frappe.has_permission(dt, "write", record, throw=True)
    frappe.has_permission("Customer", "read", customer, throw=True)
    customer_doc = frappe.get_doc("Customer", customer)

    if dt == "Quotation":
        updates = {"party_name": customer, "customer_name": customer_doc.customer_name}
    else:
        updates = {"customer": customer, "customer_name": customer_doc.customer_name}
    if address:
        updates["customer_address"] = address
    if contact:
        updates["contact_person"] = contact

    # set_value bypasses the doc lifecycle (no recalculation of prices)
    # while still using parameterized queries.
    frappe.db.set_value(dt, record, updates, update_modified=False)
    return
