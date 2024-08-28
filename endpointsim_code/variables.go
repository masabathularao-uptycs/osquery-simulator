package main

import (
	"crypto/x509"
	"flag"
	"net/http"
	"sync"
	"time"
)

var enrollClients []*http.Client
var configClients []*http.Client
var logClients []*http.Client
var distReadClients []*http.Client

// controlls the speed of actions
var enrollbatchsize = 400
var configbatchsize = 400
var distributedreadhbatchsize = 400
var print_timer_sleep_time = 120 //seconds
var assets_per_log_channel = 50
var log_channels []chan LogGoRoutineMsg
var num_log_channels int

var config_channel_count = 100
var config_channels []chan ConfigRequest

var allow_reads = true
var dist_read_channel_count = 5000
var dist_read_channels []chan DistReadRequest

// flags -- do not use. use corresponding vars. func init parses these
var domain_flag = flag.String("domain", "", "Uptycs domain")
var secret_flag = flag.String("secret", "", "Customer secret for the domain")
var name_flag = flag.String("name", "", "Name file to be used for assets")
var port_flag = flag.String("port", "", "Port to run gin server on to recieve python messages")
var count_flag = flag.Int("count", 0, "Number of assets to bring up in the process")

// variables used by nodejs simulator
var random_names []string
var random_uuids []string
var node_key *sync.Map
var counter_mux sync.Mutex
var enroll_fail_counter int
var enroll_histogram Histogram
var enroll_histogram_mux sync.Mutex
var config_histogram Histogram
var config_histogram_mux sync.Mutex
var log_histogram Histogram
var log_histogram_mux sync.Mutex
var log_fail_counter int
var config_fail_counter int
var dist_read_fail_counter int
var dist_read_histogram Histogram
var dist_read_mux sync.Mutex
var dist_write_fail_counter int
var dist_write_histogram Histogram
var dist_write_mux sync.Mutex
var reenroll_count int
var enrollurl string
var configurl string
var logurl string
var distributedreadurl string
var distributedwriteurl string

// get values instead of pointers from flags
var domain = ""
var secret = ""
var name = ""
var port = ""
var count = 0
var ca = ""
var platform_info = make_platform_info()
var caCertPool = x509.NewCertPool()

var configInterval time.Duration
var distInterval time.Duration
var enrollReqTimeout time.Duration
var configDistInterval time.Duration
var enrollDistInterval time.Duration
var distributedDistInterval time.Duration
var dist_write_status = make(map[string]string)
var dist_write_table []map[string]string
