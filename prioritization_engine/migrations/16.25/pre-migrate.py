# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("\n" * 20 + " ------- Pri-Migration Started -------")
    # cr.execute("""
    #         delete from ir_ui_view
    #         where id =(
    #         select id from ir_ui_view
    #         where id in (1930)
    #         and name = 'report_invoice_document_extended' limit 1)
    #     """)

    cr.execute("""
        update ir_ui_view set active = false where id =(
        select id from ir_ui_view
        where id in (1930)
        and name = 'report_invoice_document_extended' limit 1)
    """)
    cr.execute("""update ir_ui_view set active = true where name = 'purchase.order.form' and id = 1953""")
    cr.execute("""DELETE FROM ir_ui_view where inherit_id in (6176,1953,4216,7559);""")
    cr.execute("""DELETE FROM ir_ui_view where id in (5742,4216,4901);""")
    cr.execute("""DELETE FROM ir_cron where ir_actions_server_id in (2064, 1902);""")
    cr.execute("""ALTER TABLE payment_transaction DROP CONSTRAINT IF EXISTS payment_transaction_acquirer_id_fkey;""")


    # DELETE THE Assets
    cr.execute("""DELETE FROM ir_asset where id=94;""")
    cr.execute("""DELETE FROM ir_asset where name ilike 'sps_theme%';""")
    cr.execute("""DELETE FROM ir_asset where name ilike 'website_quote_ext%';""")
    cr.execute("""DELETE FROM ir_asset where name ilike 'website_sales%';""")
    cr.execute("""DELETE FROM ir_asset where name ilike 'payment_aquirer_cstm%';""")
    cr.execute("""DELETE FROM ir_asset where name ilike 'product_expiry_extension%';""")
    cr.execute("""DELETE FROM ir_asset where name ilike 'custom_styles%';""")
    cr.execute("""DELETE FROM ir_asset where name ilike 'in_stock_report%';""")
    cr.execute("""DELETE FROM ir_asset where name ilike 'cheque_print%';""")
    cr.execute("""DELETE FROM ir_asset where bundle ilike 'web.assets_frontend';""")


    # DELETE views
    # cr.execute("""DELETE FROM mail_template WHERE id in (13, 14, 134);""")
    cr.execute("""DELETE FROM ir_model_data WHERE name in ('email_template_edi_purchase', 'email_template_edi_purchase_done', 'email_template_edi_purchase_reminder')""")
    cr.execute("""DELETE FROM ir_ui_view WHERE key ilike 'sps_theme%' and type = 'qweb' and id not in (5508);""")
    cr.execute("""DELETE FROM ir_ui_view WHERE key ilike 'website_sales%' and type = 'qweb';""")
    cr.execute("""DELETE FROM ir_ui_view WHERE key ilike 'website_quote_ext%' and type = 'qweb';""")
    cr.execute("""DELETE FROM ir_ui_view WHERE name ilike 'product.product.form_monitor_ex';""")
    cr.execute("""DELETE FROM ir_ui_view WHERE name ilike 'product.product.form_monitor_ex';""")
    cr.execute("""DELETE FROM ir_ui_menu WHERE name->>'en_US' ilike 'My Vendor Offers';""")
    cr.execute("""DELETE FROM ir_ui_view  WHERE id in (SELECT res_id FROM ir_model_data WHERE name = 'purchase_order_form_inherit_3');""")
    cr.execute("""DELETE FROM ir_ui_view  WHERE id in (SELECT res_id FROM ir_model_data WHERE name = 'purchase_order_tree_inherit');""")
    cr.execute("""DELETE FROM ir_ui_view  WHERE id in (SELECT res_id FROM ir_model_data WHERE name = 'purchase_order_tree_sort_force');""")
    cr.execute("""DELETE FROM ir_ui_view  WHERE id in (SELECT res_id FROM ir_model_data WHERE name = 'view_picking_form_inherit_website_sale_stock_custom');""")
    cr.execute("""DELETE FROM ir_ui_menu  WHERE id in (SELECT res_id FROM ir_model_data WHERE name = 'purchase_order_menu');""")
    cr.execute("""DELETE FROM ir_ui_menu  WHERE id in (SELECT res_id FROM ir_model_data WHERE name = 'cart' and module='website_sale_require_login');""")
    cr.execute("""DELETE  FROM  ir_ui_view  WHERE name  ilike  'Odoo Studio: report_invoice_document customization'""")
    cr.execute("""DELETE  FROM  ir_ui_view  WHERE name  ilike  'Odoo Studio: purchase.order.view.tree customization'""")


    # active the inactive views
    cr.execute("""UPDATE ir_ui_view SET active=true where name ilike 'vendor.offer.purchase.order.form.main';""")
    cr.execute("""UPDATE ir_ui_view SET active=true where name ilike 'purchase.order.form.vendor.offer.inherit_3';""")
    # cr.execute("""UPDATE ir_ui_menu SET sequence = 97 WHERE name->>'en_US' ilike 'Reporting' and parent_id in (SELECT id FROM ir_ui_menu WHERE name->>'en_US' ilike 'Purchase' and parent_id is null);""")
    cr.execute("""UPDATE purchase_requisition_type set active=true WHERE name ->> 'en_US' ilike 'Purchase Tender'""")

    # client wants to remove this stage ref shared DOC
    cr.execute("""DELETE FROM crm_stage WHERE name->>'en_US' IN ('Qualified', 'Proposition', 'Won');""")

    # This View DeActivates Because of the Adjustment report throw errors (Studio View Deactivated)
    cr.execute("""update ir_ui_view set active = false where id in (5067)""")
    cr.execute("""UPDATE website_menu SET url = '/documents/pdf_content/4889' WHERE  name->>'en_US' ilike 'Surgical Equipment'""")

    ks_dashboard_ninja_queries(cr)

    _logger.info(" ------- Pri-Migration Ended -------" + "\n" * 20)







def ks_dashboard_ninja_queries(cr):
    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp1.saleforce_ac AS "SF Account #",
            rp1.name AS Customer,
            MAX(COALESCE(rp2.name, '''')) AS Business_Development,
            MAX(COALESCE(rp3.name, '''')) AS Key_Account,
            MAX(COALESCE(rp4.name, '''')) AS National_Account,
            rp1.x_studio_connected_in_ghx AS Connected_In_GHX
        FROM
            res_partner AS rp1
        LEFT JOIN
            sale_order AS so ON so.partner_id = rp1.id AND so.team_id IN (SELECT id FROM crm_team WHERE name ->> ''en_US'' = ''GHX'')
        LEFT JOIN
            res_country_state AS rcs ON rp1.state_id = rcs.id
        LEFT JOIN
            res_users AS ru1 ON rp1.user_id = ru1.id
        LEFT JOIN
            res_partner AS rp2 ON ru1.partner_id = rp2.id
        LEFT JOIN
            res_users AS ru2 ON rp1.account_manager_cust = ru2.id
        LEFT JOIN
            res_partner AS rp3 ON ru2.partner_id = rp3.id
        LEFT JOIN
            res_users AS ru3 ON so.national_account = ru3.id
        LEFT JOIN
            res_partner AS rp4 ON ru3.partner_id = rp4.id
        WHERE
            rp1.is_company = TRUE
            AND rp1.x_studio_connected_in_ghx = TRUE
            AND so.id IS NULL
        GROUP BY
            rp1.saleforce_ac, rp1.name, rp1.x_studio_connected_in_ghx
        ORDER BY
            rp1.name ASC' WHERE id = 158;
    """)



    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            ''Manual Sales'' AS source,
            SUM(CASE WHEN ct.name ->> ''en_US''= ''Sales'' THEN so.amount_total ELSE 0 END) AS amount_total
        FROM
            sale_order so
        INNER JOIN
            crm_team ct ON so.team_id = ct.id
        WHERE
            so.state = ''sale'' AND so.company_id = 1 AND EXTRACT(YEAR FROM effective_date) = EXTRACT(YEAR FROM CURRENT_DATE)
        UNION
        SELECT
            ''Other Channels'' AS source,
            SUM(CASE WHEN ct.name ->> ''en_US'' =  ''Website'' OR ct.name ->> ''en_US'' = ''My In-Stock Report'' OR ct.name ->> ''en_US'' = ''Rapid Order'' OR ct.name ->> ''en_US'' = ''GHX'' THEN so.amount_total ELSE 0 END) AS amount_total
        FROM
            sale_order so
        INNER JOIN
            crm_team ct ON so.team_id = ct.id
        WHERE
            so.state = ''sale'' AND so.company_id = 1 AND EXTRACT(YEAR FROM effective_date) = EXTRACT(YEAR FROM CURRENT_DATE)' 
        
        
        WHERE id = 162;
    """)


    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp1.saleforce_ac AS "SF Account #",
            rp1.name AS Customer,
            COALESCE(rp2.name, '''') AS Business_Development,
            COALESCE(rp3.name, '''') AS Key_Account,
            COALESCE(rp4.name, '''') AS National_Account,
            COUNT(DISTINCT so.id) AS order_count,
            SUM(so.amount_total) AS total_amount,
            TO_CHAR(MAX(so.date_order), ''YYYY-MM'') AS Most_Recent_GHX_Order
        FROM
            sale_order AS so
        JOIN
            res_partner AS rp1 ON so.partner_id = rp1.id
        LEFT JOIN
            res_country_state AS rcs ON rp1.state_id = rcs.id
        LEFT JOIN
            res_users AS ru1 ON rp1.user_id = ru1.id
        LEFT JOIN
            res_partner AS rp2 ON ru1.partner_id = rp2.id
        LEFT JOIN
            res_users AS ru2 ON rp1.account_manager_cust = ru2.id
        LEFT JOIN
            res_partner AS rp3 ON ru2.partner_id = rp3.id
        LEFT JOIN
            res_users AS ru3 ON so.national_account = ru3.id
        LEFT JOIN
            res_partner AS rp4 ON ru3.partner_id = rp4.id
        WHERE
            so.team_id IN (SELECT id FROM crm_team WHERE name ->> ''en_US'' = ''GHX'') AND ru1.id = {#UID}
        GROUP BY
            rp1.saleforce_ac, rp1.name, rp1.street, rp1.city, rcs.name, rp2.name, rp3.name, rp4.name
        ORDER BY
            Most_Recent_GHX_Order DESC, rp1.name ASC' 
        WHERE id = 121;
    """)



    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp1.saleforce_ac AS "SF Account #",
            rp1.name AS Customer,
            MAX(COALESCE(rp2.name, '''')) AS Business_Development,
            MAX(COALESCE(rp3.name, '''')) AS Key_Account,
            MAX(COALESCE(rp4.name, '''')) AS National_Account,
            rp1.x_studio_connected_in_ghx AS Connected_In_GHX
        FROM
            res_partner AS rp1
        LEFT JOIN
            sale_order AS so ON so.partner_id = rp1.id AND so.team_id IN (SELECT id FROM crm_team WHERE name ->> ''en_US'' = ''GHX'')
        LEFT JOIN
            res_country_state AS rcs ON rp1.state_id = rcs.id
        LEFT JOIN
            res_users AS ru1 ON rp1.user_id = ru1.id
        LEFT JOIN
            res_partner AS rp2 ON ru1.partner_id = rp2.id
        LEFT JOIN
            res_users AS ru2 ON rp1.account_manager_cust = ru2.id
        LEFT JOIN
            res_partner AS rp3 ON ru2.partner_id = rp3.id
        LEFT JOIN
            res_users AS ru3 ON so.national_account = ru3.id
        LEFT JOIN
            res_partner AS rp4 ON ru3.partner_id = rp4.id
        WHERE
            rp1.is_company = TRUE
            AND rp1.x_studio_connected_in_ghx = TRUE
            AND so.id IS NULL AND ru1.id = {#UID}
        GROUP BY
            rp1.saleforce_ac, rp1.name, rp1.x_studio_connected_in_ghx
        ORDER BY
            rp1.name ASC'
        WHERE id = 120;
    """)


    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp1.saleforce_ac AS "SF Account #",
            rp1.name AS Customer,
            COALESCE(rp2.name, '''') AS Business_Development,
            COALESCE(rp3.name, '''') AS Key_Account,
            COALESCE(rp4.name, '''') AS National_Account,
            COUNT(DISTINCT so.id) AS order_count,
            SUM(so.amount_total) AS total_amount,
            TO_CHAR(MAX(so.date_order), ''YYYY-MM'') AS Most_Recent_GHX_Order
        FROM
            sale_order AS so
        JOIN
            res_partner AS rp1 ON so.partner_id = rp1.id
        LEFT JOIN
            res_country_state AS rcs ON rp1.state_id = rcs.id
        LEFT JOIN
            res_users AS ru1 ON rp1.user_id = ru1.id
        LEFT JOIN
            res_partner AS rp2 ON ru1.partner_id = rp2.id
        LEFT JOIN
            res_users AS ru2 ON rp1.account_manager_cust = ru2.id
        LEFT JOIN
            res_partner AS rp3 ON ru2.partner_id = rp3.id
        LEFT JOIN
            res_users AS ru3 ON so.national_account = ru3.id
        LEFT JOIN
            res_partner AS rp4 ON ru3.partner_id = rp4.id
        WHERE
            so.team_id IN (SELECT id FROM crm_team WHERE name  ->> ''en_US'' =  ''GHX'')
            AND rp1.account_manager_cust IS NOT NULL AND ru2.id = {#UID}
        GROUP BY
            rp1.saleforce_ac, rp1.name, rp1.street, rp1.city, rcs.name, rp2.name, rp3.name, rp4.name
        ORDER BY
            Most_Recent_GHX_Order DESC, rp1.name ASC'
        WHERE id = 122;
    """)


    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp1.saleforce_ac AS "SF Account #",
            rp1.name AS Customer,
            MAX(COALESCE(rp2.name, '''')) AS Business_Development,
            MAX(COALESCE(rp3.name, '''')) AS Key_Account,
            MAX(COALESCE(rp4.name, '''')) AS National_Account,
            rp1.x_studio_connected_in_ghx AS Connected_In_GHX
        FROM
            res_partner AS rp1
        LEFT JOIN
            sale_order AS so ON so.partner_id = rp1.id AND so.team_id IN (SELECT id FROM crm_team WHERE name ->> ''en_US'' = ''GHX'')
        LEFT JOIN
            res_country_state AS rcs ON rp1.state_id = rcs.id
        LEFT JOIN
            res_users AS ru1 ON rp1.user_id = ru1.id
        LEFT JOIN
            res_partner AS rp2 ON ru1.partner_id = rp2.id
        LEFT JOIN
            res_users AS ru2 ON rp1.account_manager_cust = ru2.id
        LEFT JOIN
            res_partner AS rp3 ON ru2.partner_id = rp3.id
        LEFT JOIN
            res_users AS ru3 ON so.national_account = ru3.id
        LEFT JOIN
            res_partner AS rp4 ON ru3.partner_id = rp4.id
        WHERE
            rp1.is_company = TRUE
            AND rp1.x_studio_connected_in_ghx = TRUE
            AND so.id IS NULL
            AND rp1.account_manager_cust IS NOT NULL AND ru2.id = {#UID}
        GROUP BY
            rp1.saleforce_ac, rp1.name, rp1.x_studio_connected_in_ghx
        ORDER BY
            rp1.name ASC'
        WHERE id = 123;
    """)

    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            ''Manual Sales'' AS source,
            SUM(CASE WHEN ct.name ->> ''en_US'' = ''Sales'' THEN so.amount_total ELSE 0 END) AS amount_total
        FROM
            sale_order so
        INNER JOIN
            crm_team ct ON so.team_id = ct.id
        WHERE
            so.state = ''sale'' AND so.company_id = 1 AND EXTRACT(YEAR FROM effective_date) = EXTRACT(YEAR FROM CURRENT_DATE) AND so.account_manager IS NOT NULL AND so.account_manager != 3390 AND so.user_id != 3390 AND so.national_account != 3390
        UNION
        SELECT
            ''Other Channels'' AS source,
            SUM(CASE WHEN ct.name ->> ''en_US'' = ''Website'' OR ct.name ->> ''en_US'' = ''My In-Stock Report'' OR ct.name ->> ''en_US'' = ''Rapid Order'' OR ct.name ->> ''en_US'' = ''GHX'' THEN so.amount_total ELSE 0 END) AS amount_total
        FROM
            sale_order so
        INNER JOIN
            crm_team ct ON so.team_id = ct.id
        WHERE
            so.state = ''sale'' AND so.company_id = 1 AND EXTRACT(YEAR FROM effective_date) = EXTRACT(YEAR FROM CURRENT_DATE) AND so.account_manager IS NOT NULL AND so.account_manager != 3390 AND so.user_id != 3390 AND so.national_account != 3390'
        WHERE id = 205;
    """)


    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp1.saleforce_ac AS "SF Account #",
            rp1.name AS Customer,
            rp1.street AS Street,
            rp1.city AS City,
            rcs.name AS State,
            COALESCE(rp2.name, '''') AS Business_Development,
            COALESCE(rp3.name, '''') AS Key_Account,
            COALESCE(rp4.name, '''') AS National_Account,
            COUNT(DISTINCT so.id) AS order_count,
            SUM(so.amount_total) AS total_amount,
            MAX(so.date_order)::date AS Most_Recent_GHX_Order
        FROM
            sale_order AS so
        JOIN
            res_partner AS rp1 ON so.partner_id = rp1.id
        LEFT JOIN
            res_country_state AS rcs ON rp1.state_id = rcs.id
        LEFT JOIN
            res_users AS ru1 ON rp1.user_id = ru1.id
        LEFT JOIN
            res_partner AS rp2 ON ru1.partner_id = rp2.id
        LEFT JOIN
            res_users AS ru2 ON rp1.account_manager_cust = ru2.id
        LEFT JOIN
            res_partner AS rp3 ON ru2.partner_id = rp3.id
        LEFT JOIN
            res_users AS ru3 ON so.national_account = ru3.id
        LEFT JOIN
            res_partner AS rp4 ON ru3.partner_id = rp4.id
        WHERE
            so.team_id IN (SELECT id FROM crm_team WHERE name ->> ''en_US'' = ''GHX'')
        GROUP BY
            rp1.saleforce_ac, rp1.name, rp1.street, rp1.city, rcs.name, rp2.name, rp3.name, rp4.name
        ORDER BY
            Most_Recent_GHX_Order DESC, rp1.name ASC'
        WHERE id = 119;
    """)


    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp1.saleforce_ac AS "SF Account #",
            rp1.name AS Customer,
            MAX(rp1.street) AS Street,
            MAX(rp1.city) AS City,
            MAX(rcs.name) AS State,
            MAX(COALESCE(rp2.name, '''')) AS Business_Development,
            MAX(COALESCE(rp3.name, '''')) AS Key_Account,
            MAX(COALESCE(rp4.name, '''')) AS National_Account,
            rp1.x_studio_connected_in_ghx AS Connected_In_GHX
        FROM
            res_partner AS rp1
        LEFT JOIN
            sale_order AS so ON so.partner_id = rp1.id AND so.team_id IN (SELECT id FROM crm_team WHERE name ->> ''en_US'' = ''GHX'')
        LEFT JOIN
            res_country_state AS rcs ON rp1.state_id = rcs.id
        LEFT JOIN
            res_users AS ru1 ON rp1.user_id = ru1.id
        LEFT JOIN
            res_partner AS rp2 ON ru1.partner_id = rp2.id
        LEFT JOIN
            res_users AS ru2 ON rp1.account_manager_cust = ru2.id
        LEFT JOIN
            res_partner AS rp3 ON ru2.partner_id = rp3.id
        LEFT JOIN
            res_users AS ru3 ON so.national_account = ru3.id
        LEFT JOIN
            res_partner AS rp4 ON ru3.partner_id = rp4.id
        WHERE
            rp1.is_company = TRUE
            AND rp1.x_studio_connected_in_ghx = TRUE
            AND so.id IS NULL
        GROUP BY
            rp1.saleforce_ac, rp1.name, rp1.x_studio_connected_in_ghx
        ORDER BY
            rp1.name ASC'
        WHERE id = 118;
    """)


    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            ''Manual Sales'' AS source,
            SUM(CASE WHEN ct.name ->> ''en_US'' = ''Sales'' THEN so.amount_total ELSE 0 END) AS amount_total
        FROM
            sale_order so
        INNER JOIN
            crm_team ct ON so.team_id = ct.id
        WHERE
            so.state = ''sale'' AND so.company_id = 1 AND EXTRACT(YEAR FROM effective_date) = EXTRACT(YEAR FROM CURRENT_DATE) AND (so.user_id = 3390 OR so.account_manager = 3390 OR so.national_account = 3390)
        UNION
        SELECT
            ''Other Channels'' AS source,
            SUM(CASE WHEN ct.name ->> ''en_US'' = ''Website'' OR ct.name ->> ''en_US'' = ''My In-Stock Report'' OR ct.name ->> ''en_US'' = ''Rapid Order'' OR ct.name ->> ''en_US'' = ''GHX'' THEN so.amount_total ELSE 0 END) AS amount_total
        FROM
            sale_order so
        INNER JOIN
            crm_team ct ON so.team_id = ct.id
        WHERE
            so.state = ''sale'' AND so.company_id = 1 AND EXTRACT(YEAR FROM effective_date) = EXTRACT(YEAR FROM CURRENT_DATE) AND (so.user_id = 3390 OR so.account_manager = 3390 OR so.national_account = 3390) AND so.effective_date BETWEEN %(ks_start_date)s and %(ks_end_date)s'
        WHERE id = 194;
    """)


    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp.name,
            COUNT(cl.id)
        FROM
            crm_lead cl
        INNER JOIN
            res_users ru ON cl.user_id = ru.id
        INNER JOIN
            res_partner rp ON ru.partner_id = rp.id
        INNER JOIN
            res_groups_users_rel ug ON ru.id = ug.uid
        INNER JOIN
            res_groups rg ON ug.gid = rg.id
        WHERE
            rg.name ->> ''en_US'' = ''ACQ'' AND cl.create_date BETWEEN %(ks_start_date)s and %(ks_end_date)s
        GROUP BY
            rp.name
        ORDER BY
            rp.name'
        WHERE id = 264;
    """)


    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp.name,
            COUNT(cl.id)
        FROM
            crm_lead cl
        INNER JOIN
            res_users ru ON cl.user_id = ru.id
        INNER JOIN
            res_partner rp ON ru.partner_id = rp.id
        INNER JOIN
            res_groups_users_rel ug ON ru.id = ug.uid
        INNER JOIN
            res_groups rg ON ug.gid = rg.id
        WHERE
            rg.name ->> ''en_US'' = ''BD'' AND cl.create_date BETWEEN %(ks_start_date)s and %(ks_end_date)s
        GROUP BY
            rp.name
        ORDER BY
            rp.name'
        WHERE id = 249;
    """)

    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp.name,
            COUNT(ma.id)
        FROM
            mail_activity ma
        INNER JOIN
            res_users ru ON ma.user_id = ru.id
        INNER JOIN
            res_partner rp ON ru.partner_id = rp.id
        INNER JOIN
            res_groups_users_rel ug ON ru.id = ug.uid
        INNER JOIN
            res_groups rg ON ug.gid = rg.id
        WHERE
            rg.name ->> ''en_US'' = ''BD'' AND ma.date_done BETWEEN %(ks_start_date)s and %(ks_end_date)s
        GROUP BY
            rp.name
        ORDER BY
            rp.name'
        WHERE id = 250;
    """)


    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp.name,
            COUNT(cl.id)
        FROM
            crm_lead cl
        INNER JOIN
            res_users ru ON cl.user_id = ru.id
        INNER JOIN
            res_partner rp ON ru.partner_id = rp.id
        INNER JOIN
            res_groups_users_rel ug ON ru.id = ug.uid
        INNER JOIN
            res_groups rg ON ug.gid = rg.id
        WHERE
            rg.name ->> ''en_US'' = ''KA'' AND cl.create_date BETWEEN %(ks_start_date)s and %(ks_end_date)s
        GROUP BY
            rp.name
        ORDER BY
            rp.name'
        WHERE id = 252;
    """)


    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp.name,
            COUNT(ma.id)
        FROM
            mail_activity ma
        INNER JOIN
            res_users ru ON ma.user_id = ru.id
        INNER JOIN
            res_partner rp ON ru.partner_id = rp.id
        INNER JOIN
            res_groups_users_rel ug ON ru.id = ug.uid
        INNER JOIN
            res_groups rg ON ug.gid = rg.id
        WHERE
            rg.name ->> ''en_US'' = ''KA'' AND ma.date_done BETWEEN %(ks_start_date)s and %(ks_end_date)s
        GROUP BY
            rp.name
        ORDER BY
            rp.name'
        WHERE id = 253;
    """)


    cr.execute("""
        UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
            rp.name,
            COUNT(ma.id)
        FROM
            mail_activity ma
        INNER JOIN
            res_users ru ON ma.user_id = ru.id
        INNER JOIN
            res_partner rp ON ru.partner_id = rp.id
        INNER JOIN
            res_groups_users_rel ug ON ru.id = ug.uid
        INNER JOIN
            res_groups rg ON ug.gid = rg.id
        WHERE
            rg.name ->> ''en_US'' = ''NA'' AND ma.date_done BETWEEN %(ks_start_date)s and %(ks_end_date)s
        GROUP BY
            rp.name
        ORDER BY
            rp.name'
        WHERE id = 255;
    """)

    cr.execute("""
            UPDATE ks_dashboard_ninja_item set ks_custom_query = 'SELECT
                rp.name,
                COUNT(ma.id)
            FROM
                mail_activity ma
            INNER JOIN
                res_users ru ON ma.user_id = ru.id
            INNER JOIN
                res_partner rp ON ru.partner_id = rp.id
            INNER JOIN
                res_groups_users_rel ug ON ru.id = ug.uid
            INNER JOIN
                res_groups rg ON ug.gid = rg.id
            WHERE
                rg.name ->> ''en_US'' = ''CS'' AND ma.date_done BETWEEN %(ks_start_date)s and %(ks_end_date)s
            GROUP BY
                rp.name
            ORDER BY
                rp.name'
            WHERE id = 267;
        """)

    cr.execute("""UPDATE ir_ui_menu set action = concat('ir.actions.client,',  (SELECT id FROM ir_actions WHERE name ->> 'en_US' = 'My Dashboard' AND type = 'ir.actions.client'))  WHERE id = 1355;""")
