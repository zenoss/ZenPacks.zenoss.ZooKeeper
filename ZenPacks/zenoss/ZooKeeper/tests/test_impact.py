##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import functools

from zope.component import subscribers

from Products.Five import zcml

from Products.ZenTestCase.BaseTestCase import BaseTestCase
from Products.ZenUtils.guid.interfaces import IGUIDManager
from Products.ZenUtils.Utils import unused

from ZenPacks.zenoss.ZooKeeper.tests.utils import test_device


def require_impact(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            import ZenPacks.zenoss.Impact
            unused(ZenPacks.zenoss.Impact)
        except ImportError:
            return

        return f(*args, **kwargs)

    return wrapper


def impacts_for(thing):
    '''
    Return a two element tuple.

    First element is a list of object ids impacted by thing. Second element is
    a list of object ids impacting thing.
    '''
    try:
        from ZenPacks.zenoss.Impact.impactd.interfaces import \
            IRelationshipDataProvider

    except ImportError:
        return ([], [])

    impacted_by = []
    impacting = []

    guid_manager = IGUIDManager(thing.getDmd())
    for subscriber in subscribers([thing], IRelationshipDataProvider):
        for edge in subscriber.getEdges():
            source = guid_manager.getObject(edge.source)
            impacted = guid_manager.getObject(edge.impacted)
            if source == thing:
                impacted_by.append(impacted.id)
            elif impacted == thing:
                impacting.append(source.id)

    return (impacted_by, impacting)


class TestImpact(BaseTestCase):
    '''
    Test suite for all Impact adapters.
    '''

    def afterSetUp(self):
        super(TestImpact, self).afterSetUp()

        try:
            import ZenPacks.zenoss.DynamicView
            zcml.load_config('configure.zcml', ZenPacks.zenoss.DynamicView)
        except ImportError:
            pass

        try:
            import ZenPacks.zenoss.Impact
            zcml.load_config('meta.zcml', ZenPacks.zenoss.Impact)
            zcml.load_config('configure.zcml', ZenPacks.zenoss.Impact)
        except ImportError:
            pass

        import ZenPacks.zenoss.ZooKeeper
        zcml.load_config('configure.zcml', ZenPacks.zenoss.ZooKeeper)

    def device(self):
        if not hasattr(self, '_device'):
            self._device = test_device(self.dmd, factor=1)

        return self._device

    @require_impact
    def test_ZooKeeperImpacts(self):
        zookeeper = self.device().getObjByPath(
            'zookeepers/zookeeper0')

        impacts, impacted_by = impacts_for(zookeeper)
        self.assertTrue('zookeeper_test_device' in impacted_by)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestImpact))
    return suite
