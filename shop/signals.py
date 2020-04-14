from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_init
from django.dispatch import receiver
from django.utils import timezone

from shop.models import TorBridge


@receiver(post_save, sender=TorBridge)
def post_save_tor_bridge(sender, instance: TorBridge, **kwargs):
    created = kwargs.get('created')

    if instance.previous_status != instance.status or created:
        if instance.status == sender.ACTIVE:
            instance.process_activation()
        elif instance.status == sender.SUSPENDED:
            instance.process_suspension()

    if created:
        print("Tor Bridge created - setting random port...")
        instance.port = instance.host.get_random_port()

        instance.suspend_after = timezone.make_aware(timezone.datetime.max,
                                                     timezone.get_default_timezone())

        # time.sleep(3)

        # now also create a ShopInvoice for new tor bridge
        # inv = ShopLnInvoice.create_invoice("Invoice for Tor Bridge ID: {}".format(instance.id),
        #                                    4711)  # ToDo.. use pricing here
        #
        # inv.tor_bridge = instance
        # inv.save()

        # instance.tor_invoices.add(inv)
        instance.save()


#
# @receiver(post_save, sender=ShopLnInvoice)
# def post_save_shop_invoice(sender, instance: ShopLnInvoice, **kwargs):
#     created = kwargs.get('created')
#
#     if created:
#         print("A Shop Invoice was created: {}".format(instance))
#         if not instance.tor_bridge:
#             print("But no tor bridge associated yet.. returning")
#             return
#
#     if instance.tor_bridge:
#         if instance.tor_bridge.status == TorBridge.INITIAL:
#             print("Tor bridge belonging to this invoice exists and is still "
#                   "in state INITIAL: {}".format(instance.tor_bridge))
#
#             # ToDo(frennkie) Signals are blocking.. (in contrast to celery)
#
#             # set to pending
#             instance.tor_bridge.status = TorBridge.PENDING
#             instance.tor_bridge.save()
#
#             # create invoice on backend
#             instance.create_backend_invoice()
#             instance.save()


@receiver(post_init, sender=TorBridge)
def remember_status_tor_bridge(sender, instance: TorBridge, **kwargs):
    instance.previous_status = instance.status


def create_default_operator_group(sender, **kwargs):
    operation_group_name = getattr(settings, 'SHOP_OPERATOR_GROUP_NAME', 'operators')

    obj, was_created = Group.objects.get_or_create(name=operation_group_name)
    if not was_created:
        return  # exists already - no further action

    shop_models = apps.get_app_config('shop').get_models()
    for model in shop_models:
        content_type = ContentType.objects.get_for_model(model)
        all_permissions = Permission.objects.filter(content_type=content_type)
        for p in all_permissions:
            obj.permissions.add(p)