package main

import (
	"fmt"
	"time"
)


/*
func main() {
	out := make(chan int)
	in := make(chan int)

	// Create 3 `multiplyByTwo` goroutines.
	go multiplyByTwo(in, out,1)
	go multiplyByTwo(in, out,2)
	go multiplyByTwo(in, out,3	)

	// Up till this point, none of the created goroutines actually do
	// anything, since they are all waiting for the `in` channel to
	// receive some data, we can send this in another goroutine
	go func() {
		in <- 1
		in <- 2
		in <- 3
		in <- 4
	}()

	// Now we wait for each result to come in
	fmt.Println(<-out)
	fmt.Println(<-out)
	fmt.Println(<-out)
	fmt.Println(<-out)
}

func multiplyByTwo(in <-chan int, out chan<- int,test int) {
	fmt.Println("Initializing goroutine...")
	for {
	    fmt.Println("Handled by",test)
		num := <-in
		result := num * 2
		out <- result
	}
	fmt.Println("closing")
}
*/


func fast(num int, out chan<- int) {
	result := num * 2
	time.Sleep(5 * time.Millisecond)
	out <- result

}

func slow(num int, out chan<- int) {
	result := num * 2
	time.Sleep(15 * time.Millisecond)
	out <- result
}

func main() {
	out1 := make(chan int)
	out2 := make(chan int)

	// we start both fast and slow in different
	// goroutines with different channels
	go fast(2, out1)
	go slow(3, out2)

	// perform some action depending on which channel
	// receives information first
	select {
	case res := <-out1:
		fmt.Println("fast finished first, result:", res)
	case res := <-out2:
		fmt.Println("slow finished first, result:", res)
	}
	
		select {
	case res := <-out1:
		fmt.Println("fast finished first, result:", res)
	case res := <-out2:
		fmt.Println("slow finished first, result:", res)
	}
	
	
time.Sleep(time.Second *10)
}