/*
 * Copyright (c) 2017 Uptycs, Inc. All rights reserved
 */

'use strict';

const fs = require('fs');
const path = require('path');
const https = require('https');
const readline = require('readline');
const rp = require('request-promise-native');
const measured = require('measured');
const mm = require('moment');
const uuid = require('uuid');
const util = require('util');
const zlib = require('zlib');
const dgram = require('dgram');
var os = require("os");
//require('request-debug')(rp); //oncomment this to get debugs in osx_logX.out that have all requests + responses
const optimist = require('optimist')
  .usage('\nUsage: $0 [options]')
  .options('h', { alias: 'help', type: 'boolean', describe: 'Print usage' })
  .options('c', { alias: 'count', default: 1, describe: 'Number of endpoints to simulate' })
    .options('p', { alias: 'port',  describe: 'udp port on which it receives trigger from python app' })

    .options('v', { alias: 'version', default: '2.9.0', describe: 'Playback version' })
  .options('f', { alias: 'file', default: 'ubuntu16-ep.log.gz', describe: 'Playback file' })
    .options('n', { alias: 'name', default: 'names.txt', describe: 'Names File' })
    .options('d', { alias: 'domain', default: 'app', describe: 'Uptycs SaaS domain' })
  .options('s', { alias: 'secret', default: '11111111-1111-1111-1111-111111111111', describe: 'Uptycs secret' });

const argv = optimist.argv;
if (argv.help) {
  console.log(optimist.help());
  process.exit();
}
if (argv.count < 1 || !argv.version || !argv.file || !argv.secret || !argv.domain) {
  console.error(optimist.help());
  process.exit(1);
}

const playbackFile = path.resolve(__dirname, argv.version, argv.file);
if (!fs.existsSync(playbackFile)) {
  console.error('ERROR: Playback file does not exist: ' + playbackFile);
  process.exit(1);
}

const parts = argv.file.split('-');
if (parts.length < 2) {
  console.error('ERROR: Invalid playback file. Expected format: <platform>-<name>.log');
  process.exit(1);
}

const startUnix = mm().unix();
console.info("First")
let platform,
  platform_like,
  version,
  platform_type = 0x08;
switch (parts[0]) {
  case 'ubuntu12':
    platform = 'ubuntu';
    platform_like = 'debian';
    version = '12.04.5 LTS (Precise Pangolin)';
    break;
  case 'ubuntu14':
    platform = 'ubuntu';
    platform_like = 'debian';
    version = '14.04.5 LTS (Trusty Tahr)';
    break;
  case 'ubuntu16':
    platform = 'ubuntu';
    platform_like = 'debian';
    version = '16.04.3 LTS (Xenial Xerus)';
    break;
  case 'rhel6':
    platform = 'rhel';
    platform_like = 'rhel';
    version = 'RedHat 6.5';
    break;
  case 'rhel7':
    platform = 'rhel';
    platform_like = 'rhel';
    version = 'RedHat 7.0';
    break;
  case 'osx':
    platform = 'darwin';
    platform_like = 'darwin';
    version = '10.12.6';
    platform_type = 0x10;
    break;
  default:
    console.error('ERROR: Unsupported platform: ' + parts[0]);
    process.exit(1);
}

const ca = fs.readFileSync(path.resolve(__dirname, 'ca.crt'));
const processes = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'processes.json')));
processes.items.forEach(e => delete e.upt_asset_id);
//console.info('try your luck')
const uptime = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'uptime.json')));
uptime.items.forEach(e => delete e.upt_asset_id);

const AGENTS = {};

function getRequestOptions(type, assetIndex, body) {
  let agent = AGENTS[type + assetIndex];
  //console.info('agent',agent)
  if (!agent) {
    agent = new https.Agent({
      keepAlive: true,
      keepAliveMsecs: 159000,
      maxSockets: 1
    });
      //console.info('agent',agent)

      AGENTS[type + assetIndex] = agent;
  }
  const options = {
    agent,
    ca,
    timeout: 159000,
    strictSSL: true,
    ecdhCurve: 'auto',
    time: true,
    method: 'POST',
    uri:`https://${argv.domain}.uptycs.io/agent/${type}`,
    json: true,
    resolveWithFullResponse: true,
    headers: {"user-agent": "osquery/3.3.2.45-Uptycs"},
    body
  };
  return options;
}

const HOST_NAMES = {};

function getEnrollRequest(assetIndex, uuidv4) {
  const rand = Math.floor(Math.random() * (RANDOM_NAMES.length - 1));
  const hostname = RANDOM_NAMES[rand].toLowerCase() + '-' + os.hostname() + '-' + argv.port + '-' + assetIndex + '.uptycs.com';
  HOST_NAMES[assetIndex] = hostname;
  return {
    enroll_secret: argv.secret,
    host_identifier: uuidv4,
    platform_type,
    host_details: {
      os_version: {
        _id: hostname,
        codename: 'blah',
        major: '12',
        minor: '34',
        name: platform,
        patch: '0',
        platform,
        platform_like,
        version
      },
      osquery_info: {
        build_distro: 'xenial',
        build_platform: 'ubuntu',
        config_hash: '',
        config_valid: '0',
        extensions: 'active',
        instance_id: uuid.v4(),
        pid: '17881',
        start_time: '' + mm().unix(),
        uuidv4,
        version: '2.10.1-Uptycs',
        watcher: '17875'
      },
      platform_info: {
        address: '0xf000',
        date: '07/07/2016',
        extra: '',
        revision: '1.12',
        size: '16777216',
        vendor: 'HP',
        version: 'N82 Ver. 01.12',
        volume_size: '0'
      },
      system_info: {
        computer_name: hostname,
        hostname,
        local_hostname: hostname  ,
        cpu_brand: 'Intel(R) Core(TM) i7-6700HQ CPU @ 2.60GHz\u0000\u0000\u0000\u0000\u0000\u0000\u0000',
        cpu_logical_cores: '8',
        cpu_physical_cores: '8',
        cpu_subtype: '94',
        cpu_type: '6',
        hardware_model: 'HP ZBook Studio G3',
        hardware_serial: 'CND60233F6',
        hardware_vendor: 'HP',
        hardware_version: ' ',
        physical_memory: '25199255552',
        uuid: uuidv4
      }
    }
  };
}

const UUID = {},
  NODE_KEY = {};
const enrollTimer = new measured.Timer(),
  failedEnrollCounter = new measured.Counter();

function get_host_uuid(length) {
    var hostname = os.hostname()
    while (hostname.length < length) {
        hostname = '0' + hostname;
    }
    hostname = hostname.substring(hostname.length-4).toUpperCase();
    return hostname

}

async function enroll(assetIndex, uuidv4_arg) {
  var uuidv4=''
  if ( uuidv4_arg === undefined) {
      var ruuidv4 = uuid.v4().toUpperCase();
      uuidv4=ruuidv4.substring(0,9) + 'ABCD'  + ruuidv4.substring(13)
      console.log('Created ' + uuidv4)
  }else{
    uuidv4 = uuidv4_arg
    console.log('Reusing ' + uuidv4)
  }
  try {
    /*
    const uuidv4 = uuid.v4().toUpperCase();
    */
    const enrollRequest = getEnrollRequest(assetIndex, uuidv4);
    const res = await rp(getRequestOptions('enroll', assetIndex, enrollRequest));
    //console.info("rnroll response",res.statusCode)
    if (res.statusCode !== 200) {
      throw new Error('Invalid enroll response: ' + res.statusCode);
    }
    if (!res.body.node_key || (res.body.hasOwnProperty('node_invalid') && res.body.node_invalid)) {
      throw new Error('Invalid node key or node is invalid: ' + JSON.stringify(res.body));
    }
    //console.info("just begore calling log")
    console.log(new Date() + ': Enrollment complete: ' + assetIndex);

    enrollTimer.update(res.elapsedTime);

    UUID[assetIndex] = uuidv4;
    NODE_KEY[assetIndex] = res.body.node_key;

    setImmediate(config, assetIndex);

    //console.log(NODE_KEY[assetIndex]) 
      setImmediate(read, assetIndex);

  } catch (err) {
    console.error('WARN: Got error for enroll request: ' + assetIndex, err);
    failedEnrollCounter.inc();
    console.log(new Date() + ': Re-trying enroll')
    setTimeout(enroll, 30000, assetIndex, uuidv4);

  }
}

const LOG_STARTED = {};
const configTimer = new measured.Timer(),
  failedConfigCounter = new measured.Counter();

async function config(assetIndex) {
  //console.info("configuring for ------",assetIndex)
  try {
    const node_key = NODE_KEY[assetIndex];

    //const outgoing = getRequestOptions('config', assetIndex, { node_key });
    //console.log(util.inspect(outgoing, {showHidden: false, depth: null}));

    const res = await rp(getRequestOptions('config', assetIndex, { node_key }));
    // console.log(util.inspect(res, {showHidden: false, depth: null}))

    if (res.statusCode !== 200) {
      throw new Error('Invalid config response: ' + res.statusCode);
    }

    configTimer.update(res.elapsedTime);

    if (!LOG_STARTED[assetIndex]) {
      setImmediate(log, assetIndex, mm().unix(), 0, true);
      LOG_STARTED[assetIndex] = true;
      //console.info("LOG_STARTED ++++++",assetIndex)

    }

  } catch (err) {
    //console.error('WARN: Got error for config request: ' + assetIndex, err);
    console.error('WARN: Got error for config request: ' + assetIndex);
    failedConfigCounter.inc();
    //return setImmediate(config, assetIndex);
  }

  if (NODE_KEY[assetIndex]) {
    setTimeout(config, 300000, assetIndex);
  }
}


var observe = require('observe')
var object = {Events:[],Alarms:[]}
var observer = observe(object)
var evecount = 1;

async function sockfun(assetIndex) {
  //console.info("I am inside sockfun")
    let ts = 0;

    const server = dgram.createSocket('udp4');
    server.on('error', (err) => {
        console.log(`server error:\n${err.stack}`);
        server.close();
    });

    server.on('message', (msg, rinfo) => {
        var s =`${msg}`
        let body
        const tstamp =parseInt(s.slice(0,10))
        const udpcon=s.slice(10,)
        //const body = JSON.parse(udpcon);
        body = JSON.parse(udpcon);
        console.log(body)
        if (evecount % 2 == 1) {
            observer.get('Events').push({tstamp, body})
            while(observer.subject.Alarms.length > 0) {
                observer.subject.Alarms.pop();
            }

        }

        if (evecount % 2 == 0) {
            observer.get('Alarms').push({tstamp, body})
            while(observer.subject.Events.length > 0) {
                observer.subject.Events.pop();
            }

        }
        evecount=evecount+1
        //console.log(observer.subject.Events.length,observer.subject.Alarms.length)

    });

    server.on('listening', () => {
        const address = server.address();
        console.log(`server listening ${address.address}:${address.port}`);
    });

    //server.bind(41234);
    server.bind(argv.port);

}




const readTimer = new measured.Timer(),
  failedReadCounter = new measured.Counter();

async function read(assetIndex) {
  try {
    const node_key = NODE_KEY[assetIndex];
    const res = await rp(getRequestOptions('distributed_read', assetIndex, { node_key }));
    if (res.statusCode !== 200) {
      throw new Error('Invalid distributed read response: ' + res.statusCode);
    } else if (res.body && res.body.hasOwnProperty('queries')) {
      try {
        const dresp = { queries: {}, statuses: { info: '0' }, node_key };
        if (res.body.queries[Object.keys(res.body.queries)[0]] === 'select * from uptime') {
          dresp.queries[Object.keys(res.body.queries)[0]] = uptime.items;
        } else {
          dresp.queries[Object.keys(res.body.queries)[0]] = processes.items;
        }
        const res1 = await rp(getRequestOptions('distributed_write', assetIndex, dresp));
        console.log("Response code of Distributed write for asset " + NODE_KEY[assetIndex]+ " is",res1.statusCode);
        if (res1.statusCode !== 200) {
          throw new Error('Invalid distributed write response: ' + res1.statusCode);
        }
      } catch (err) {
        console.error('WARN: Got error for distributed write request: ' + assetIndex, err);
      }
    }
    readTimer.update(res.elapsedTime);
  } catch (err) {
    console.error('WARN: Got error for distributed read request: ' + assetIndex, err);
    failedReadCounter.inc();
  }
if (NODE_KEY[assetIndex]) {
  console.log('\n' + new Date());
  console.log(`I am resending distributed read for ${NODE_KEY[assetIndex]}` )
  setImmediate(read, assetIndex);
}else{
  console.log(`I am not calling distributed read for ${NODE_KEY[assetIndex]}`)
}

}

async function test(){
    console.info("inside test")
}

let done = 0;
const CURRENT_OFFSET = {};
const logTimer = new measured.Timer(),
  failedLogCounter = new measured.Counter();

async function tes(logmsg) {
    //const res = await rp(logmsg);
    // console.log(JSON.stringify(logmsg))
    let Res
    Res = await rp(logmsg);
    //console.info("....... IMP.....",res.statusCode)
    if (Res.statusCode !== 200) {
        throw new Error('Invalid log response: ' + Res.statusCode);
        failedLogCounter.inc();

    }

    logTimer.update(Res.elapsedTime);


}

async function log(assetIndex, startTime, logOffset, retry) {
  //console.info(assetIndex, startTime, logOffset, retry)
    //console.log(LOGS.length);
    var sleep = require('system-sleep');
    //console.info("no of elements in LOGs",LOGS.length,assetIndex)
    
    //pairs=NODE_KEY[assetIndex].split(':')
    //pairs[2]="kubernetes"
    //pairs[3]="kubernetes"
    //NODE_KEY[assetIndex]=pairs.join(':')
    //console.log("Node key",NODE_KEY[assetIndex])
    observer.on('change', function(change) {
    
        if(change.property[0] === 'Events' && change.type === 'added') {
            var s = change.count>1 ? 's' : '' // plural
            //console.log("My client: ",assetIndex ," ",change.count)

            var newlyAdd= observer.subject.Events.slice(change.index, change.index+change.count)
            //console.info(newlyAdd)
            var arrayLength = newlyAdd.length;
            //console.info("arrayLength",arrayLength,assetIndex)
            for (var i = 0; i < arrayLength; i++) {
              var singleEvent=newlyAdd[i]
                //console.info(singleEvent)
                var uuidv4 = UUID[assetIndex];
                var hostname = HOST_NAMES[assetIndex];
                var body = singleEvent.body
                //console.info(singleEvent.body)
                //console.info(NODE_KEY[assetIndex])
                //console.info(body.node_key)
                //var pairs;
                //pairs=NODE_KEY[assetIndex].split(':')
                //pairs[2]="okta"
                //pairs[3]="okta"
                //NODE_KEY[assetIndex]=pairs.join(':')
                body.node_key = NODE_KEY[assetIndex];
                //console.info(body.node_key)
                //console.info(singleEvent.tstamp)

                if (body.data && Array.isArray(body.data)) {
                    body.data.forEach(record => {
                        if (record.hostIdentifier) {
                            record.hostIdentifier = uuidv4;
                        }
                        if (record.unixTime) {
                            record.unixTime = singleEvent.tstamp;
                        }
                        if (record.hostname) {
                            record.hostname = hostname;
                        }
                        if (record.snapshot && Array.isArray(record.snapshot)) {
                            record.snapshot.forEach(snapshot => {
                                if (snapshot.hostname) {
                                    snapshot.hostname = hostname;
                                }
                            });
                        }
                        //console.log(record);
                    });
                }

                if (body.tables) {
                   Object.entries(body.tables).forEach(([table, chunk]) => {
                      if (chunk && Array.isArray(chunk)) {
                         chunk.forEach(record => {
                         if (record.hostIdentifier) {
                            record.hostIdentifier = uuidv4;
                        }
                        if (record.unixTime) {
                            record.unixTime = singleEvent.tstamp;
                        }
                        if (record.hostname) {
                            record.hostname = hostname;
                        }
                        if (record.snapshot && Array.isArray(record.snapshot)) {
                            record.snapshot.forEach(snapshot => {
                                if (snapshot.hostname) {
                                    snapshot.hostname = hostname;
                                }
                            });
                        }
                        //console.log(record);
                    });
                  }});
                }

            }

        }



            if(change.property[0] === 'Alarms' && change.type === 'added') {

                var s = change.count>1 ? 's' : '' // plural
                //console.log("My client: ",assetIndex ," ",change.count)

                var newlyAdd= observer.subject.Alarms.slice(change.index, change.index+change.count)
                //console.info(newlyAdd)
                var arrayLength = newlyAdd.length;
                //console.info("arrayLength",arrayLength,assetIndex)
                for (var i = 0; i < arrayLength; i++) {
                    var singleEvent=newlyAdd[i]
                    //console.info(singleEvent)
                    var uuidv4 = UUID[assetIndex];
                    var hostname = HOST_NAMES[assetIndex];
                    var body = singleEvent.body
                    //console.info(singleEvent.body)
                    //console.info(NODE_KEY[assetIndex])
                    //console.info(body.node_key)
                    //var pairs;
                    //pairs=NODE_KEY[assetIndex].split(':')
                    //pairs[2]="okta"
                    //pairs[3]="okta"
                    //NODE_KEY[assetIndex]=pairs.join(':')
                    body.node_key = NODE_KEY[assetIndex];
                    //console.info(body.node_key)
                    //console.info(singleEvent.tstamp)

                    if (body.data && Array.isArray(body.data)) {
                        body.data.forEach(record => {
                            if (record.hostIdentifier) {
                                record.hostIdentifier = uuidv4;
                            }
                            if (record.unixTime) {
                                record.unixTime = singleEvent.tstamp;
                            }
                            if (record.hostname) {
                                record.hostname = hostname;
                            }
                            if (record.snapshot && Array.isArray(record.snapshot)) {
                                record.snapshot.forEach(snapshot => {
                                    if (snapshot.hostname) {
                                        snapshot.hostname = hostname;
                                    }
                                });
                            }
                        });
                    }

                    if (body.tables) {
                      Object.entries(body.tables).forEach(([table, chunk]) => {
                      if (chunk && Array.isArray(chunk)) {
                         chunk.forEach(record => {
                         if (record.hostIdentifier) {
                            record.hostIdentifier = uuidv4;
                        }
                        if (record.unixTime) {
                            record.unixTime = singleEvent.tstamp;
                        }
                        if (record.hostname) {
                            record.hostname = hostname;
                        }
                        if (record.snapshot && Array.isArray(record.snapshot)) {
                            record.snapshot.forEach(snapshot => {
                                if (snapshot.hostname) {
                                    snapshot.hostname = hostname;
                                }
                            });
                        }
                        //console.log(record);
                    });
                  }});
                  }

                }

            }

                // console.log(body)
                var gds=getRequestOptions('log', assetIndex, body)
                tes(gds)

    }
    )

    //console.info("end of function")
}

const RANDOM_NAMES = [];

function init() {
  console.log(new Date() + ': Loading random names'+argv.name);

  const nameReader = readline.createInterface({
      //input: fs.createReadStream(path.resolve(__dirname, 'names1.txt'))
      input: fs.createReadStream(path.resolve(__dirname, argv.name))
  });
  nameReader.on('line', line => RANDOM_NAMES.push(line));
  //nameReader.on('close', readPlayback);
  nameReader.on('close', startEnrollment);
}

const LOGS = [];

function readPlayback() {
  console.log(new Date() + ': Loading playback file');

  const logReader = readline.createInterface({
    input: fs.createReadStream(playbackFile).pipe(zlib.createGunzip())
  });

  let start, offset;
  logReader.on('line', line => {
    if (offset) {
      const body = JSON.parse(line);
      //LOGS.push({ offset, body });
      offset = null;
    } else {
      offset = mm(line, 'YYYY-MM-DD HH:mm:ss').unix();
      if (!start) {
        start = offset - 1;
      }
      offset -= start;
    }
  });

  logReader.on('close', startEnrollment);
}

let LOGS_COUNT;

function startEnrollment() {
  LOGS_COUNT = LOGS.length;
  console.log(new Date() + ': Scheduling enrollment');
  for (let i = 0; i < argv.count; i++) {
    setTimeout(enroll, i * 100, i);
  }
  setImmediate(sockfun,1);

    setInterval(printTimers, 120000);
}

function averageOffset() {
  let sum = 0;
  Object.values(CURRENT_OFFSET).forEach(o => sum += o);
  return sum / argv.count;
}

function printTimers() {
  console.log('\n' + new Date() + '. Duration: ' + (mm().unix() - startUnix) + ' secs');
  console.log('Offsets: ' + LOGS_COUNT + '. Average offset: ' + averageOffset());
  printTimer('Enroll', enrollTimer, failedEnrollCounter);
  printTimer('Config', configTimer, failedConfigCounter);
  printTimer('Read', readTimer, failedReadCounter);
  printTimer('Log', logTimer, failedLogCounter);
}

function printTimer(type, timer, counter) {
  const h = timer.toJSON().histogram;
  console.log(
    '    ' +
    type +
    ', Failed: ' +
    counter.toJSON() +
    ', Count: ' +
    h.count +
    ', Min: ' +
    round(h.min) +
    ', Max: ' +
    round(h.max) +
    ', Mean: ' +
    round(h.mean) +
    ', Median: ' +
    round(h.median) +
    ', 75%: ' +
    round(h.p75) +
    ', 95%: ' +
    round(h.p95) +
    ', 99%: ' +
    round(h.p99) +
    ', 99.9%: ' +
    round(h.p999)
  );
}

function round(i) {
  return Math.round(i * 100) / 100;
}
console.info("last")
init();
