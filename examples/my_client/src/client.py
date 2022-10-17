import asyncio
import argparse
import random
import sys

import nexus

latencies = []

async def query(server, input_size, expected_start_time):
    user_id = random.randint(0, 2 ** 31 - 1)
    async with nexus.AsyncClient(server, user_id) as client:
        _send_time, _recv_time, reply = await client.request(b' ' * input_size)

    cur_time = time.time_ns() / 1000.

    latency = cur_time - expected_start_time

    latencies.append(latency)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iat", help="Interarrival Time (us)", type=float)
    parser.add_argument("--ln_sigma", help="Lognormal Sigma", type=float)
    parser.add_argument("--model_weights", help="Model weights", type=str)
    parser.add_argument("--input_sizes", help="Input sizes (bytes)", type=str)
    parser.add_argument("--port_start", help="First port of frontend", default=9000, type=int)
    parser.add_argument("--server", help="Frontend server", default="localhost", type=str)
    parser.add_argument("--num_jobs", help="Number of jobs to submit", type=int)
    parser.add_argument("--output", help="Path to output", type=str)
    args = parser.parse_args()

    log_normal_mu = math.log(args.iat) - args.ln_sigma * args.ln_sigma / 2.

    model_weights = [float(x) for x in args.model_weights.split(',')]
    input_sizes = [int(x) for x in args.input_sizes.split(',')]
    model_hosts = ['{}:{}'.format(args.server, port) for port in range(args.port_start, args.port_start + len(model_weights))]

    next_submit_time = 0
    num_submitted_jobs = 0
    background_tasks = set()
    start_time = time.time_ns() / 1000.

    while num_submitted_jobs < args.num_jobs:
        cur_time = time.time_ns() / 1000.
        time_elasped = cur_time - start_time

        if time_elasped >= next_submit_time:
            model_chosen = random.choices(range(len(model_weights)), weights=model_weights)

            task = asyncio.create_task(query(model_hosts[model_chosen], input_sizes[model_chosen], start_time + next_submit_time))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)

            num_submitted_jobs += 1

            next_submit_time += random.lognormvariate(log_normal_mu, args.ln_sigma)

    await asyncio.wait(background_tasks)

    end_time = time.time_ns / 1000.

    latencies.sort()

    mean = mean(latencies)
    mean_sqr = mean([latency * latency for latency in latencies]);

    sd = sqrt((mean_sqr - mean * mean) * (len(latencies) / (len(latencies) - 1)));

    p50 = latencies[len(latencies) / 2];
    p90 = latencies[len(latencies) * 0.90];
    p95 = latencies[len(latencies) * 0.95];
    p99 = latencies[len(latencies) * 0.99];
    max_latency = max(latencies);

    with open(args.output, 'a') as f:
        f.write('{},{},{},{},{},{},{},{},{}\n'.format(args.iat, (end_time - start_time) / 1000., mean, p50, p90, p95, p99, max_latency, sd))


if __name__ == "__main__":
    asyncio.run(main())
