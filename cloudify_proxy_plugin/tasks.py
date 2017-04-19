# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import sys

import proxy_common

from cloudify import ctx
from cloudify import exceptions
from cloudify import manager

from cloudify.decorators import operation


@operation
def wait_for_deployment(deployment_id, **kwargs):
    ctx.logger.info("Entering wait_for_deployment event.")
    ctx.logger.info("Using deployment %s" % deployment_id)
    if not deployment_id:
        raise exceptions.NonRecoverableError(
            "Deployment ID not specified.")

    client = manager.get_rest_client()
    timeout = ctx.node.properties['timeout']
    proxy_common.poll_until_with_timeout(
        proxy_common.check_if_deployment_is_ready(
            client, deployment_id),
        expected_result=True,
        timeout=timeout)

    ctx.logger.info("Exiting wait_for_deployment event.")


@operation
def inherit_deployment_attributes(deployment_id, **kwargs):
    ctx.logger.info("Entering obtain_outputs event.")
    client = manager.get_rest_client()
    outputs = ctx.node.properties['inherit_outputs']
    ctx.logger.info("Outputs to inherit: {0}."
                    .format(str(outputs)))
    ctx.logger.info('deployment id %s' % deployment_id)
    inherit_inputs = ctx.node.properties['inherit_inputs']
    ctx.instance.runtime_properties.update({
        'inherit_outputs': outputs,
        'deployment_id': deployment_id
    })
    try:
        if inherit_inputs:
            _inputs = client.deployments.get(deployment_id)['inputs']
            ctx.instance.runtime_properties.update(
                {'proxy_deployment_inputs': _inputs})
        deployment_outputs = client.deployments.outputs.get(
            deployment_id)['outputs']
        ctx.logger.info("Available deployment outputs {0}."
                        .format(str(deployment_outputs)))
        ctx.logger.info("Available runtime properties: {0}.".format(
            str(ctx.instance.runtime_properties.keys())
        ))
        for key in outputs:
            ctx.instance.runtime_properties.update(
                {key: deployment_outputs.get(key)}
            )
    except Exception as ex:
        ctx.logger.error(
            "Caught exception during obtaining "
            "deployment outputs {0} {1}"
            .format(sys.exc_info()[0], str(ex)))
        raise exceptions.NonRecoverableError(
            "Caught exception during obtaining "
            "deployment outputs {0} {1}. Available runtime properties {2}"
            .format(sys.exc_info()[0], str(ex),
                    str(ctx.instance.runtime_properties.keys())))
    ctx.logger.info("Exiting obtain_outputs event.")


@operation
def cleanup(**kwargs):
    ctx.logger.info("Entering cleanup_outputs event.")
    outputs = ctx.instance.runtime_properties.get('inherit_outputs', [])
    if ('proxy_deployment_inputs' in
            ctx.instance.runtime_properties):
        del ctx.instance.runtime_properties['proxy_deployment_inputs']
    for key in outputs:
        if key in ctx.instance.runtime_properties:
            del ctx.instance.runtime_properties[key]
    ctx.logger.info("Exiting cleanup_outputs event.")


@operation
def get_outputs(**kwargs):
#  if (ctx.target.node._node.type!='cloudify.nodes.DeploymentProxy'):
#    raise (NonRecoverableError('invalid target: must connect to DeploymentProxy type'))

  for output in ctx.target.node.properties['inherit_outputs']:
    ctx.source.instance.runtime_properties[output]=ctx.target.instance.runtime_properties[output]