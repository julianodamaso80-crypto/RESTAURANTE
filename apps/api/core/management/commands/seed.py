import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Popula o banco com dados realistas para demo e desenvolvimento"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Limpar dados existentes antes de sedar")
        parser.add_argument(
            "--tenant",
            type=str,
            default="all",
            help="Sedar apenas tenant especifico (burguer|napoli|all)",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_data()

        with transaction.atomic():
            self.stdout.write("Criando Burguer Palace...")
            tenant_bp, stores_bp = self._create_burguer_palace()

            self.stdout.write("Criando Pizza Napoli...")
            self._create_pizza_napoli()

            self.stdout.write("Criando clientes e historico...")
            self._create_customers_and_history(tenant_bp, stores_bp[0])

            self.stdout.write("Calculando RFV...")
            self._trigger_rfv_calculation(tenant_bp)

            self.stdout.write("Criando segmentos e campanhas demo...")
            self._create_crm_demo(tenant_bp, stores_bp[0])

        self.stdout.write(self.style.SUCCESS("Seed concluido com sucesso!"))
        self._print_summary()

    def _clear_data(self):
        """Remove dados de seed anteriores (preserva superusers)."""
        from crm.models import Campaign, CampaignTemplate, CustomerSegment, TenantBillingQuota
        from orders.models import Order
        from tenants.models import Tenant, User

        self.stdout.write("Limpando dados anteriores...")
        seed_tenants = Tenant.objects.filter(name__in=["Burguer Palace", "Pizza Napoli"])
        # Delete models with PROTECT FKs first (order matters):
        Campaign.objects.filter(tenant__in=seed_tenants).delete()
        CustomerSegment.objects.filter(tenant__in=seed_tenants).delete()
        CampaignTemplate.objects.filter(tenant__in=seed_tenants).delete()
        TenantBillingQuota.objects.filter(tenant__in=seed_tenants).delete()
        Order.objects.filter(tenant__in=seed_tenants).delete()
        # Now safe to cascade-delete everything else
        seed_tenants.delete()
        # Delete seed-created users (preserves superusers and non-seed users)
        seed_emails = ["owner@burguerpala.ce", "manager.paulista@burguerpala.ce", "operator1@burguerpala.ce"]
        User.objects.filter(email__in=seed_emails).delete()

    def _create_burguer_palace(self):
        from tenants.models import Company, Membership, Store, Tenant, User

        tenant = Tenant.objects.create(name="Burguer Palace", slug="burguer-palace")
        company = Company.objects.create(name="Burguer Palace LTDA", tenant=tenant, slug="burguer-palace-ltda")

        stores = []
        store_data = [
            ("Burguer Palace - Paulista", "paulista"),
            ("Burguer Palace - Jardins", "jardins"),
            ("Burguer Palace - Santos", "santos"),
        ]
        for store_name, slug in store_data:
            store = Store.objects.create(name=store_name, company=company, slug=slug)
            stores.append(store)

        # Criar users
        owner = User.objects.create_user(email="owner@burguerpala.ce", password="demo123", name="Carlos Owner")
        owner.is_staff = True
        owner.save(update_fields=["is_staff"])
        Membership.objects.create(user=owner, tenant=tenant)

        manager = User.objects.create_user(
            email="manager.paulista@burguerpala.ce", password="demo123", name="Ana Manager"
        )
        manager.is_staff = True
        manager.save(update_fields=["is_staff"])
        Membership.objects.create(user=manager, tenant=tenant, company=company, store=stores[0])

        operator = User.objects.create_user(
            email="operator1@burguerpala.ce", password="demo123", name="Pedro Operator"
        )
        Membership.objects.create(user=operator, tenant=tenant, company=company, store=stores[0])

        # Criar catalogo
        self._create_catalog_burguer(tenant, company, stores[0])

        # Criar estoque
        self._create_stock_burguer(stores[0])

        # Criar KDS
        self._create_kds_burguer(stores[0])

        return tenant, stores

    def _create_catalog_burguer(self, tenant, company, store):
        from catalog.models import (
            Catalog,
            CatalogStatus,
            Category,
            ModifierGroup,
            ModifierOption,
            Product,
            ProductChannelMap,
        )

        catalog = Catalog.objects.create(
            tenant=tenant,
            company=company,
            store=store,
            name="Cardapio Delivery",
            status=CatalogStatus.ACTIVE,
            channels=["IFOOD", "OWN"],
        )

        # Hamburgueres
        cat_hamburguer = Category.objects.create(
            catalog=catalog, name="Hamburgueres", status=CatalogStatus.ACTIVE, display_order=1
        )

        produtos_hamburguer = [
            ("X-Burguer Classico", 2890, 1),
            ("X-Bacon Duplo", 3890, 2),
            ("Veggie Burger", 3290, 3),
        ]
        for name, price, order in produtos_hamburguer:
            p = Product.objects.create(
                category=cat_hamburguer,
                name=name,
                price_cents=price,
                status=CatalogStatus.ACTIVE,
                display_order=order,
            )
            slug = name.lower().replace(" ", "-")
            ProductChannelMap.objects.create(product=p, channel="IFOOD", external_id=f"ifood-{slug}")

            if name == "X-Burguer Classico":
                mg1 = ModifierGroup.objects.create(
                    product=p, name="Ponto da carne", min_choices=1, max_choices=1, display_order=1
                )
                for opt_name, delta, is_def in [
                    ("Mal passado", 0, False),
                    ("Ao ponto", 0, True),
                    ("Bem passado", 0, False),
                ]:
                    ModifierOption.objects.create(
                        group=mg1, name=opt_name, price_delta_cents=delta, is_default=is_def
                    )
                mg2 = ModifierGroup.objects.create(
                    product=p, name="Adicionais", min_choices=0, max_choices=3, display_order=2
                )
                for opt_name, delta in [("Bacon", 300), ("Ovo", 200), ("Cheddar extra", 300)]:
                    ModifierOption.objects.create(group=mg2, name=opt_name, price_delta_cents=delta)

        # Porcoes
        cat_porcoes = Category.objects.create(
            catalog=catalog, name="Porcoes", status=CatalogStatus.ACTIVE, display_order=2
        )
        for name, price, order in [("Batata Frita P", 1490, 1), ("Batata Frita G", 2290, 2), ("Onion Rings", 1890, 3)]:
            Product.objects.create(
                category=cat_porcoes,
                name=name,
                price_cents=price,
                status=CatalogStatus.ACTIVE,
                display_order=order,
            )

        # Bebidas
        cat_bebidas = Category.objects.create(
            catalog=catalog, name="Bebidas", status=CatalogStatus.ACTIVE, display_order=3
        )
        for name, price, order in [
            ("Refrigerante Lata 350ml", 690, 1),
            ("Suco Natural 400ml", 1190, 2),
            ("Agua Mineral", 450, 3),
            ("Milkshake", 1990, 4),
        ]:
            Product.objects.create(
                category=cat_bebidas,
                name=name,
                price_cents=price,
                status=CatalogStatus.ACTIVE,
                display_order=order,
            )

    def _create_stock_burguer(self, store):
        from stock.models import MovementType, StockItem, StockUnit
        from stock.tasks import recalculate_stock_level

        items_data = [
            ("Carne bovina 180g", StockUnit.UN, Decimal("20"), Decimal("100")),
            ("Pao de hamburguer", StockUnit.UN, Decimal("30"), Decimal("150")),
            ("Alface", StockUnit.KG, Decimal("2.0"), Decimal("5.0")),
            ("Queijo fatiado", StockUnit.KG, Decimal("1.5"), Decimal("4.0")),
            ("Bacon", StockUnit.KG, Decimal("1.0"), Decimal("3.0")),
            ("Batata congelada", StockUnit.KG, Decimal("5.0"), Decimal("20.0")),
            # Item intencional abaixo do minimo (demo de alerta)
            ("Catchup sache", StockUnit.UN, Decimal("50"), Decimal("10")),
        ]

        from stock.models import StockMovement

        for name, unit, minimum, initial_qty in items_data:
            item = StockItem.objects.create(store=store, name=name, unit=unit, minimum_stock=minimum)
            StockMovement.objects.create(
                stock_item=item,
                store=store,
                type=MovementType.ENTRADA,
                quantity=initial_qty,
                notes="Estoque inicial (seed)",
            )

        # Recalcular saldos sincronamente
        for item in StockItem.objects.filter(store=store):
            recalculate_stock_level(str(item.id))

    def _create_kds_burguer(self, store):
        from kds.models import KDSStation, KDSStationCategory

        KDSStation.objects.create(store=store, name="Chapa", category=KDSStationCategory.GRILL, display_order=1)
        KDSStation.objects.create(
            store=store, name="Frios/Montagem", category=KDSStationCategory.COLD, display_order=2
        )
        KDSStation.objects.create(
            store=store, name="Bebidas/Expedicao", category=KDSStationCategory.DRINKS, display_order=3
        )

    def _create_pizza_napoli(self):
        from catalog.models import Catalog, CatalogStatus, Category, ModifierGroup, ModifierOption, Product
        from tenants.models import Company, Store, Tenant

        tenant = Tenant.objects.create(name="Pizza Napoli", slug="pizza-napoli")
        company = Company.objects.create(name="Pizza Napoli LTDA", tenant=tenant, slug="pizza-napoli-ltda")
        store = Store.objects.create(name="Pizza Napoli - Centro", company=company, slug="centro")

        catalog = Catalog.objects.create(
            tenant=tenant,
            company=company,
            store=store,
            name="Cardapio",
            status=CatalogStatus.ACTIVE,
        )
        cat = Category.objects.create(
            catalog=catalog, name="Pizzas Tradicionais", status=CatalogStatus.ACTIVE, display_order=1
        )
        for name, price in [("Margherita G", 4990), ("Calabresa G", 5290), ("Quatro Queijos G", 5890)]:
            p = Product.objects.create(category=cat, name=name, price_cents=price, status=CatalogStatus.ACTIVE)
            mg = ModifierGroup.objects.create(product=p, name="Tamanho", min_choices=1, max_choices=1)
            ModifierOption.objects.create(group=mg, name="P", price_delta_cents=-1500)
            ModifierOption.objects.create(group=mg, name="M", price_delta_cents=-800)
            ModifierOption.objects.create(group=mg, name="G", price_delta_cents=0, is_default=True)

        # Bebidas
        cat_bebidas = Category.objects.create(
            catalog=catalog, name="Bebidas", status=CatalogStatus.ACTIVE, display_order=2
        )
        for name, price in [("Refrigerante 2L", 1290), ("Suco de Laranja", 990)]:
            Product.objects.create(
                category=cat_bebidas, name=name, price_cents=price, status=CatalogStatus.ACTIVE
            )

        return tenant

    def _create_customers_and_history(self, tenant, store):
        from cdp.models import ConsentChannel, ConsentRecord, ConsentStatus, Customer, CustomerIdentity, IdentityType
        from orders.enums import OrderChannel, OrderStatus, OrderType
        from orders.models import Order, OrderItem

        nomes = [
            ("Joao Silva", "+5511991110001"),
            ("Maria Santos", "+5511991110002"),
            ("Pedro Oliveira", "+5511991110003"),
            ("Ana Costa", "+5511991110004"),
            ("Carlos Souza", "+5511991110005"),
            ("Fernanda Lima", "+5511991110006"),
            ("Lucas Ferreira", "+5511991110007"),
            ("Juliana Pereira", "+5511991110008"),
            ("Rafael Alves", "+5511991110009"),
            ("Camila Rodrigues", "+5511991110010"),
            ("Bruno Nascimento", "+5511991110011"),
            ("Larissa Carvalho", "+5511991110012"),
            ("Thiago Martins", "+5511991110013"),
            ("Priscila Araujo", "+5511991110014"),
            ("Diego Melo", "+5511991110015"),
            ("Vanessa Barbosa", "+5511991110016"),
            ("Gabriel Rocha", "+5511991110017"),
            ("Amanda Dias", "+5511991110018"),
            ("Mateus Gomes", "+5511991110019"),
            ("Patricia Castro", "+5511991110020"),
            ("Rodrigo Monteiro", "+5511991110021"),
            ("Beatriz Cardoso", "+5511991110022"),
            ("Felipe Ramos", "+5511991110023"),
            ("Natalia Freitas", "+5511991110024"),
            ("Andre Pinto", "+5511991110025"),
            ("Tatiana Cruz", "+5511991110026"),
            ("Caio Lopes", "+5511991110027"),
            ("Renata Teixeira", "+5511991110028"),
            ("Eduardo Nunes", "+5511991110029"),
            ("Daniela Cunha", "+5511991110030"),
        ]

        # Perfis: (nome_idx, n_pedidos, dias_desde_ultimo, valor_medio_cents)
        perfis = [
            # VIP (5 clientes)
            (0, 15, 3, 4500),
            (1, 12, 7, 5200),
            (2, 10, 5, 3900),
            (3, 11, 2, 4800),
            (4, 14, 1, 6000),
            # Regulares (10 clientes)
            (5, 5, 15, 3200),
            (6, 4, 20, 2800),
            (7, 6, 12, 3500),
            (8, 3, 25, 2500),
            (9, 7, 8, 4100),
            (10, 4, 18, 3000),
            (11, 5, 22, 2900),
            (12, 3, 30, 2600),
            (13, 6, 10, 3800),
            (14, 4, 28, 2700),
            # Inativos (10 clientes)
            (15, 2, 60, 2200),
            (16, 1, 75, 1800),
            (17, 3, 50, 2100),
            (18, 2, 45, 2300),
            (19, 1, 90, 1500),
            (20, 2, 55, 2000),
            (21, 1, 80, 1700),
            (22, 3, 48, 2400),
            (23, 2, 65, 1900),
            (24, 1, 70, 1600),
            # Novos (5 clientes)
            (25, 1, 2, 3100),
            (26, 1, 1, 2800),
            (27, 1, 3, 3500),
            (28, 1, 5, 2900),
            (29, 1, 4, 3200),
        ]

        consent_whatsapp = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19}
        consent_email = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14}

        now = timezone.now()
        order_counter = 1

        for idx, n_pedidos, dias_ultimo, valor_medio in perfis:
            nome, phone = nomes[idx]
            customer = Customer.objects.create(
                tenant=tenant,
                name=nome,
                phone=phone,
                email=f"cliente{idx + 1}@email.com",
            )
            CustomerIdentity.objects.create(
                customer=customer,
                type=IdentityType.PHONE,
                value=phone,
                is_verified=True,
                source="seed",
            )

            if idx in consent_whatsapp:
                ConsentRecord.objects.create(
                    customer=customer,
                    channel=ConsentChannel.WHATSAPP,
                    status=ConsentStatus.GRANTED,
                    source="seed",
                )
            if idx in consent_email:
                ConsentRecord.objects.create(
                    customer=customer,
                    channel=ConsentChannel.EMAIL,
                    status=ConsentStatus.GRANTED,
                    source="seed",
                )

            # Pedidos historicos
            for pedido_n in range(n_pedidos):
                if pedido_n == 0:
                    dias_atras = dias_ultimo
                else:
                    dias_atras = dias_ultimo + (pedido_n * random.randint(7, 21))

                pedido_dt = now - timedelta(
                    days=dias_atras,
                    hours=random.randint(11, 22),
                    minutes=random.randint(0, 59),
                )

                total = valor_medio + random.randint(-500, 500)
                order = Order.objects.create(
                    tenant=tenant,
                    store=store,
                    display_number=f"#{order_counter:04d}",
                    channel=random.choice([OrderChannel.OWN, OrderChannel.IFOOD]),
                    order_type=OrderType.DELIVERY,
                    status=OrderStatus.DELIVERED,
                    subtotal_cents=total,
                    total_cents=total,
                    created_at=pedido_dt,
                    confirmed_at=pedido_dt + timedelta(minutes=2),
                    delivered_at=pedido_dt + timedelta(minutes=random.randint(30, 60)),
                    notes=phone,
                )
                OrderItem.objects.create(
                    order=order,
                    name="X-Burguer Classico",
                    quantity=random.randint(1, 3),
                    unit_price_cents=2890,
                    total_cents=total,
                )
                order_counter += 1

        self.stdout.write(f"  Criados {order_counter - 1} pedidos historicos")

    def _trigger_rfv_calculation(self, tenant):
        """Calcula RFV sincronamente para todos os customers do tenant."""
        from cdp.models import Customer
        from cdp.tasks import recalculate_customer_rfv

        customers = Customer.objects.filter(tenant=tenant)
        for customer in customers:
            recalculate_customer_rfv(str(customer.id))
        self.stdout.write(f"  RFV calculado para {customers.count()} clientes")

    def _create_crm_demo(self, tenant, store):
        from crm.models import Campaign, CampaignStatus, CampaignTemplate, CustomerSegment, TenantBillingQuota

        CustomerSegment.objects.create(
            tenant=tenant,
            name="Clientes VIP",
            description="Frequencia >= 5 pedidos",
            criteria=[{"criteria": "RFV_FREQUENCY_GTE", "value": 5}],
        )
        CustomerSegment.objects.create(
            tenant=tenant,
            name="Win-back 30 dias",
            description="Sem pedido ha 30+ dias",
            criteria=[{"criteria": "NO_ORDER_SINCE_DAYS", "value": 30}],
        )
        CustomerSegment.objects.create(
            tenant=tenant,
            name="Com WhatsApp",
            criteria=[{"criteria": "HAS_CONSENT", "value": "WHATSAPP"}],
        )

        template = CampaignTemplate.objects.create(
            tenant=tenant,
            name="Promocao Fim de Semana",
            channel="WHATSAPP",
            body="Oi {{name}}! Este fim de semana tem X-Burguer Duplo por R$34,90. Peca pelo app!",
        )

        seg_vip = CustomerSegment.objects.get(tenant=tenant, name="Clientes VIP")

        Campaign.objects.create(
            tenant=tenant,
            store=store,
            name="Black Friday Burguer",
            segment=seg_vip,
            template=template,
            status=CampaignStatus.DRAFT,
        )

        TenantBillingQuota.objects.get_or_create(
            tenant=tenant,
            defaults={"max_contacts": 500, "current_period_contacts": 0},
        )

        self.stdout.write("  Segmentos, template e campanha demo criados")

    def _print_summary(self):
        from cdp.models import Customer
        from orders.models import Order
        from tenants.models import Store, Tenant

        self.stdout.write("\nResumo do seed:")
        for tenant in Tenant.objects.filter(name__in=["Burguer Palace", "Pizza Napoli"]):
            stores = Store.objects.filter(company__tenant=tenant).count()
            customers = Customer.objects.filter(tenant=tenant).count()
            orders = Order.objects.filter(tenant=tenant).count()
            self.stdout.write(f"  {tenant.name}: {stores} lojas, {customers} clientes, {orders} pedidos")

        self.stdout.write("\nCredenciais de acesso:")
        self.stdout.write("  owner@burguerpala.ce / demo123")
        self.stdout.write("  manager.paulista@burguerpala.ce / demo123")
        self.stdout.write("  http://localhost:8000/admin/ (criar superuser separado)")
