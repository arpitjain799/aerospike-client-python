# -*- coding: utf-8 -*-

import pytest
import sys
from .test_base_class import TestBaseClass

from aerospike import exception as e
from aerospike_helpers import expressions as exp
from .as_status_codes import AerospikeStatus

aerospike = pytest.importorskip("aerospike")
try:
    import aerospike
except:
    print("Please install aerospike python client.")
    sys.exit(1)


class TestQueryPartition(TestBaseClass):

    @pytest.fixture(autouse=True)
    def setup(self, request, as_connection):
        self.test_ns = 'test'
        self.test_set = 'demo'

        self.partition_1000_count = 0
        self.partition_1001_count = 0
        self.partition_1002_count = 0
        self.partition_1003_count = 0
        
        as_connection.truncate(self.test_ns, None, 0)

        for i in range(1, 100000):
            put = 0
            key = (self.test_ns, self.test_set, str(i))
            rec_partition = as_connection.get_key_partition_id(self.test_ns, self.test_set, str(i))

            if rec_partition == 1000:
                self.partition_1000_count += 1
                put = 1 
            if rec_partition == 1001:
                self.partition_1001_count += 1
                put = 1 
            if rec_partition == 1002:
                self.partition_1002_count += 1
                put = 1 
            if rec_partition == 1003:
                self.partition_1003_count += 1
                put = 1 
            if put:
                rec = {
                    'i': i,
                    's': 'xyz',
                    'l': [2, 4, 8, 16, 32, None, 128, 256],
                    'm': {'partition': rec_partition, 'b': 4, 'c': 8, 'd': 16}
                }
                as_connection.put(key, rec)
        # print(f"{self.partition_1000_count} records are put in partition 1000, \
        #         {self.partition_1001_count} records are put in partition 1001, \
        #         {self.partition_1002_count} records are put in partition 1002, \
        #         {self.partition_1003_count} records are put in partition 1003")

        def teardown():
            for i in range(1, 100000):
                put = 0
                key = ('test', u'demo', str(i))
                rec_partition = as_connection.get_key_partition_id(self.test_ns, self.test_set, str(i))

                if rec_partition == 1000:
                    self.partition_1000_count += 1
                    put = 1 
                if rec_partition == 1001:
                    self.partition_1001_count += 1
                    put = 1 
                if rec_partition == 1002:
                    self.partition_1002_count += 1
                    put = 1 
                if rec_partition == 1003:
                    self.partition_1003_count += 1
                    put = 1 
                if put:
                   as_connection.remove(key)

        request.addfinalizer(teardown)

    def test_query_partition_with_existent_ns_and_set(self):

        records = []
        partition_filter = {'begin': 1000, 'count': 1}
        policy = {'max_retries': 100,
                        'max_records': 1000,
                        'partition_filter': partition_filter,
                        'records_per_second': 4000}

        def callback(part_id,input_tuple):
            _, _, record = input_tuple
            records.append(record)

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        query_obj.foreach(callback, policy)

        assert len(records) == self.partition_1000_count

    def test_query_partition_with_filter(self):

        records = []

        partition_filter = {'begin': 1000, 'count': 4}

        expr = exp.Eq(exp.MapGetByKey(None, aerospike.MAP_RETURN_VALUE, exp.ResultType.INTEGER, "partition", exp.MapBin("m")), 1002)

        policy = {'max_retries': 100,
                        'max_records': 1000,
                        'expressions': expr.compile(),
                        'partition_filter': partition_filter,
                        'records_per_second': 4000}

        def callback(part_id,input_tuple):
            _, _, record = input_tuple
            records.append(record)

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        query_obj.foreach(callback, policy)

        assert len(records) == self.partition_1002_count

    def test_query_partition_with_filter_zero(self):

        records = []

        partition_filter = {'begin': 1000, 'count': 1}

        expr = exp.Eq(exp.MapGetByKey(None, aerospike.MAP_RETURN_VALUE, exp.ResultType.INTEGER, "partition", exp.MapBin("m")), 1002)

        policy = {'max_retries': 100,
                        'max_records': 1000,
                        'expressions': expr.compile(),
                        'partition_filter': partition_filter,
                        'records_per_second': 4000}

        def callback(part_id,input_tuple):
            _, _, record = input_tuple
            records.append(record)

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        query_obj.foreach(callback, policy)

        assert len(records) == 0

    def test_query_partition_with_existent_ns_and_none_set(self):

        records = []

        def callback(part_id,input_tuple):
            _, _, record = input_tuple
            records.append(record)

        query_obj = self.as_connection.query(self.test_ns, None)

        query_obj.foreach(callback, {'partition_filter': {'begin': 1000, 'count': 1}})

        assert len(records) == self.partition_1000_count

    def test_query_partition_with_timeout_policy(self):

        ns = 'test'
        st = 'demo'

        records = []

        def callback(part_id,input_tuple):
            _, _, record = input_tuple
            records.append(record)

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        query_obj.foreach(callback, {'timeout': 1001, 'partition_filter': {'begin': 1000, 'count': 1}})

        assert len(records) == self.partition_1000_count

    # NOTE: This could fail if node record counts are small and unbalanced across nodes.
    @pytest.mark.xfail(reason="Might fail depending on record count and distribution.")
    def test_query_partition_with_max_records_policy(self):

        ns = 'test'
        st = 'demo'

        records = []

        max_records = self.partition_1000_count // 2

        def callback(part_id,input_tuple):
            _, _, record = input_tuple
            records.append(record)

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        query_obj.foreach(callback, {'max_records': max_records, 'partition_filter': {'begin': 1000, 'count': 1}})
        assert len(records) == self.partition_1000_count // 2

    @pytest.mark.xfail(reason="Might fail depending on record count and distribution.")
    def test_query_partition_with_all_records_policy(self):
    
        ns = 'test'
        st = 'demo'

        records = []

        max_records = self.partition_1000_count + \
                        self.partition_1001_count + \
                        self.partition_1002_count + \
                        self.partition_1003_count

        def callback(part_id,input_tuple):
            _, _, record = input_tuple
            records.append(record)

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        query_obj.foreach(callback, {'max_records': max_records, 'partition_filter': {'begin': 1000, 'count': 4}})
        assert len(records) == max_records

    def test_query_partition_with_socket_timeout_policy(self):

        ns = 'test'
        st = 'demo'

        records = []

        def callback(part_id,input_tuple):
            _, _, record = input_tuple
            records.append(record)

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        query_obj.foreach(callback, {'socket_timeout': 9876, 'partition_filter': {'begin': 1000, 'count': 1}})

        assert len(records) == self.partition_1000_count

    def test_query_partition_with_callback_returning_false(self):
        """
            Invoke query() with callback function returns false
        """

        records = []

        def callback(part_id,input_tuple):
            _, _, record = input_tuple
            if len(records) == 10:
                return False
            records.append(record)

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        query_obj.foreach(callback, {'timeout': 1000, 'partition_filter': {'begin': 1000, 'count': 1}})
        assert len(records) == 10

    def test_query_partition_with_results_method(self):

        ns = 'test'
        st = 'demo'

        query_obj = self.as_connection.query(ns, st)

        records = query_obj.results({'partition_filter': {'begin': 1001, 'count': 1}})
        assert len(records) == self.partition_1001_count

    def test_resume_part_query(self):
        """
            Resume a query using foreach.
        """
        records = 0
        resumed_records = 0

        def callback(part_id, input_tuple):
            nonlocal records
            if records == 5:
                return False
            records += 1

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        query_obj.foreach(callback, {'partition_filter': {'begin': 1001, 'count': 1}})

        assert records == 5

        partition_status = query_obj.get_partitions_status()

        def resume_callback(part_id, input_tuple):
            nonlocal resumed_records
            resumed_records += 1

        query_obj2 = self.as_connection.query(self.test_ns, self.test_set)

        policy = {
            'partition_filter': {
                'begin': 1001,
                'count': 1,
                "partition_status": partition_status
            },
        }

        query_obj2.foreach(resume_callback, policy)

        assert records + resumed_records == self.partition_1001_count

    def test_resume_query_results(self):

        """
            Resume a query using results.
        """
        records = 0

        def callback(part_id, input_tuple):
            nonlocal records
            if records == 5:
                return False
            records += 1

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        query_obj.foreach(callback, {'partition_filter': {'begin': 1001, 'count': 1}})

        assert records == 5

        partition_status = query_obj.get_partitions_status()

        query_obj2 = self.as_connection.query(self.test_ns, self.test_set)

        policy = {
            'partition_filter': {
                'begin': 1001,
                'count': 1,
                "partition_status": partition_status
            },
        }

        results = query_obj2.results(policy)

        assert records + len(results) == self.partition_1001_count

    def test_query_partition_with_non_existent_ns_and_set(self):

        ns = 'namespace'
        st = 'set'

        records = []
        query_obj = self.as_connection.query(ns, st)

        def callback(part_id,input_tuple):
            _, _, record = input_tuple
            records.append(record)

        with pytest.raises(e.ClientError) as err_info:
            query_obj.foreach(callback, {'partition_filter': {'begin': 1001, 'count': 1}})
        err_code = err_info.value.code
        assert err_code == AerospikeStatus.AEROSPIKE_ERR_CLIENT

    def test_query_partition_with_callback_contains_error(self):

        def callback(part_id,input_tuple):
            raise Exception("callback error")

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        with pytest.raises(e.ClientError) as err_info:
            query_obj.foreach(callback, {'timeout': 1000, 'partition_filter': {'begin': 1001, 'count': 1}})

        err_code = err_info.value.code
        assert err_code == AerospikeStatus.AEROSPIKE_ERR_CLIENT

    def test_query_partition_with_callback_non_callable(self):
        records = []

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        with pytest.raises(e.ClientError) as err_info:
            query_obj.foreach(5, {'partition_filter': {'begin': 1001, 'count': 1}})

        err_code = err_info.value.code
        assert err_code == AerospikeStatus.AEROSPIKE_ERR_CLIENT # TODO this should be an err param

    def test_query_partition_with_callback_wrong_number_of_args(self):

        def callback(input_tuple):
            pass

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        with pytest.raises(e.ClientError) as err_info:
            query_obj.foreach(callback, {'partition_filter': {'begin': 1001, 'count': 1}})

        err_code = err_info.value.code
        assert err_code == AerospikeStatus.AEROSPIKE_ERR_CLIENT

    #@pytest.mark.xfail(reason="Might fail, server may return less than what asked for.")
    def test_query_partition_status_with_existent_ns_and_set(self):

        records = []
        query_page_size = [5]
        query_count = [0]
        query_pages = [5]

        max_records = self.partition_1000_count + \
            self.partition_1001_count + \
            self.partition_1002_count + \
            self.partition_1003_count
        break_count = [5]

        # partition_status = [{id:(id, init, done, digest)},(),...]
        def init(id):
            return 0;
        def done(id):
            return 0;
        def digest(id):
            return bytearray([0]*20);

        partition_status = {id:(id, init(id), done(id), digest(id)) for id in range (1000, 1004,1)}

        partition_filter = {'begin': 1000, 'count': 4, 'partition_status': partition_status}

        policy = {'max_records': query_page_size[0],
                'partition_filter': partition_filter,
                'records_per_second': 4000}

        def callback(part_id, input_tuple):
            if(input_tuple == None):
                return True #query complete
            (key, _, record) = input_tuple
            partition_status.update({part_id:(part_id, 1, 0, key[3])})
            records.append(record)
            query_count[0] = query_count[0] + 1
            break_count[0] = break_count[0] - 1
            if(break_count[0] == 0):
                return False 

        query_obj = self.as_connection.query(self.test_ns, self.test_set)

        i = 0
        for i in range(query_pages[0]):
            query_obj.foreach(callback, policy)
            if query_obj.is_done() == True: 
                break
            if(break_count[0] == 0):
                break

        assert len(records) == query_count[0]

        query_page_size = [1000]
        query_count[0] = 0
        break_count[0] = 1000

        partition_filter = {'begin': 1000, 'count': 4, 'partition_status': partition_status}

        policy = {'max_records': query_page_size[0],
                'partition_filter': partition_filter,
                'records_per_second': 4000}

        new_query_obj = self.as_connection.query(self.test_ns, self.test_set)
        i = 0
        for i in range(query_pages[0]):
            new_query_obj.foreach(callback, policy)
            if new_query_obj.is_done() == True: 
                break
            if(break_count[0] == 0):
                break

        assert len(records) == max_records
