#!/usr/bin/python

import os
import random
import time
import traceback
from concurrent import futures
import random

import grpc

from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

import demo_pb2
import demo_pb2_grpc

_LISTEN_HOST = "[::]"
_LISTEN_PORT = "9556"

_THREAD_POOL_SIZE = 256

from logger import getJSONLogger
logger = getJSONLogger('adservice-v2-server')


class AdServiceV2(demo_pb2_grpc.AdServiceV2Servicer, health_pb2_grpc.HealthServicer):

    def Check(self, request, context):
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.SERVING)
    
    def Watch(self, request, context):
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.UNIMPLEMENTED)

    def GetAds(self, request, context):
        # Get list product from productcatalogservice
        channel = grpc.insecure_channel("productcatalogservice:3550")
        stub = demo_pb2_grpc.ProductCatalogServiceStub(channel)
        
        response = stub.ListProducts(demo_pb2.Empty())
        # get 3 random result
        random_products = random.choices(response.products, k=3)
        url= "/product/{}"
        text = "AdV2 - Items with 25% discount!"
        
        ads = [demo_pb2.Ad(redirect_url=url.format(p.id), text=text) for p in random_products]
        
        return demo_pb2.AdResponse(ads=ads)


if __name__ == "__main__":
    logger.info("initializing adservice-v2")
    server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=_THREAD_POOL_SIZE))

    ad_service_v2_servicer = AdServiceV2()

    health_pb2_grpc.add_HealthServicer_to_server(ad_service_v2_servicer, server)
    demo_pb2_grpc.add_AdServiceV2Servicer_to_server(ad_service_v2_servicer, server)

    print("Server starting on port {}...".format(_LISTEN_PORT))
    server.add_insecure_port("{}:{}".format(_LISTEN_HOST,_LISTEN_PORT))
    server.start()

    # Keep thread alive
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)