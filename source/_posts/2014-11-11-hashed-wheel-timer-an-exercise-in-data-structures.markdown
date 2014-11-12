---
layout: post
title: "Hashed Wheel Timer - An exercise in data structures"
date: 2014-11-11 20:22:55 -0800
comments: true
author: Rajiv
categories: [DataStructures]
---
## Hashed wheel timers - A short intro.

The Hashed wheel timer is a very interesting data structure used widely especially in network servers. Their low over memory over head and reasonable efficiency guarantees are a good match for servers handling millions of connections with a timer per connection. We will not spend too much time describing how they work, instead we will look at a few implementations and try to evaulate their relative trade-offs. More information about hashed-wheel-timers can be found [here](http://www.cs.columbia.edu/~nahum/w6998/papers/sosp87-timing-wheels.pdf).
<!-- more -->

Let's quickly recollect the basic data structures of a hashed wheel timer:
<p align="center">
<img src="/images/hashed-wheel-timer-basic.svg" width="500">
</p>

The basic data structure looks like a hashmap with separate chaining with lists. Each bucket represents a fixed number of ticks. When a timer is added to the wheel we calculate which bucket it should fall into. Though any hashing scheme would do, we usually just travel forward from the current time pointer one bucket at a time, till we have consumed enough ticks for our timeout to have just triggered. We then insert the timer into the list for that bucket. Given that we have a finite number of buckets, we might have to circle around the timer wheel a few times before we can insert our timer. We will need to store this information with the timer. This is typically stored as a ```remainingRounds``` variable.

The first draft of an interface for out fictional timer is:

``` cpp TimerWheel.h
// A Timer is uniquely identified by an id.
// We don't care how this id is generated.
Timer* add_timer(uint64_t delay, uint64_t id);  // Assume that the delay is in nanos for now.
void cancel_timer(Timer* timer);
// Write the list of expired ids into the input array, assuming it is long enough.
// Returning a list of expired timers instead of calling the expiry processing inline
// helps in ensuring the integrity of internal timer data structures
// since all we need to do is ensure that the timer structures are
// consistent before and after a function call, but not during.
void expire_timers(uint64_t* ids, uint64_t size);
}
```
Usually a timer is implemented with a more generic interface with some kind of a ```Runnable``` task per timer that is executed upon timer expiry. We have made things a lot more specific and require that each timer has an unique id. We also leave the execution of code corresponding to each expired timer up to the user of the library. We could use some other identifier instead of an id. For eg: A pointer to a per connection structure if the timers are for closing stale connections.

So the absolute minimum data we need to have in our timers is:
``` cpp Timer.cpp
struct Timer {
  uint64_t id;  // Or some other unique identifier. 8 bytes should be enough.
  uint64_t deadline;
  uint64_t remaining_rounds;
};
```

Given this basic scheme let's look at some of the ways we could implement the interface we showed earlier
#####1. Linked list of timers per bucket.
<p align="center">
<img src="/images/hashed-wheel-timer-linked-list.svg" width="500">
</p>

Each bucket simply points to an intrusive doubly linked list of timers. Our timer struct looks like:

``` cpp Timer.cpp
enum PreviousType {Timer, TimerWheel};

struct Timer {
  uint64_t id;
  uint64_t deadline;
  uint64_t remaining_rounds;
  Timer* next;
  // A tagged union since the previous could be either a
  // pointer to a timer or a pointer to the bucket.
  union {
    Timer* previous;
    TimerBucket* wheel;
  }
  enum PreviousType previousType;
};
```
Our algorithms look like
``` cpp TimerWheel.cpp
Timer* add_timer(uint64_t delay, uint64_t id) {
  Timer* timer = create_timer(delay, id);
  TimerBucket* bucket = findBucket(timer);
  // Just prepend the timer to the linked list at the bucket;
  insert_into_bucket(bucket_id, timer);
  return timer;
}

void cancel_timer(Timer* timer) {
  // Since the timer is part of a doubly linked list,
  // just delete it from the linked list and free the memory.
}

// Write the list of expired ids into the input array, assuming it is long enough.
void expire_timers(uint64_t* ids, uint64_t size) {
  // If it wasn't already clear this is pseudo code.
  deadline = calculate_deadline();
  int num_ids_added = 0;
  for (bucket : every bucket that could contain expired timers) {
    for (timer : bucket) {
      if (0 >= timer->remainingRounds && timer->deadline <= deadline) {
        append_to_ids(ids, size, &num_ids_added, timer->id);
        cancel_timer(timer);
      } else {
        --timer->remainingRounds;
      }
    }
  }
}
```
So our algorithm characteristics in brief are:

1.  To add a timer, just prepend it to the appropriate linked list - ```O(1)```
2.  To cancel a timer - delete it from the doubly linked list - ```O(1)```
3.  To clean up all expired timers - Travel list of timers and delete expired ones - ```O(expired timers)```. The actual time depends on how many timers hashed onto a bucket. We can put some bounds on this number with general hash table math.

###### Comments on implementation.

This is our base line. We have significant memory over head in terms of previous/next pointers on our timers. It's pretty terrible that we have to ```malloc()``` and ```free()``` on each ```add_timer()``` and ```cancel_timer()``` call. Of course the ```O(1)``` calls also hide the fact that we are traversing a linked list during timer expiry which is pretty terrible.

#####2. Vector of timer pointers per bucket.
<p align="center">
<img src="/images/hashed-wheel-timer-vector.svg" width="500">
</p>

Instead of an intrusive linked list we can just store a vector of pointers to timers. We can grow this vector as needed. If memory is not a concern we could allocate a large enough array so that growing is never needed (though still accounted for). Our timer struct now looks like:

``` cpp Timer.cpp

struct Timer {
  uint64_t id;
  uint64_t deadline;
  uint64_t remaining_rounds;
}; 

struct TimerBucket {
  int size;
  int capacity;
  // Array of pointers to timers.
  Timer* timers[];
};

```
Our algorithms look like
``` cpp TimerWheel.cpp
Timer add_timer(uint64_t delay, uint64_t id) {
  Timer* timer = create_timer(delay, id);
  TimerBucket* bucket = findBucket(timer);
  // Just append the timer to the vector for the bucket.
  append_to_bucket(bucket, timer);
  return timer;
}

void cancel_timer(Timer* timer) {
  // Since the timer is part of a vector, we can't just adjust a couple pointers.
  // Since ordering within the vector is not important, we copy the last
  // timer pointer (if the deleted timer wasn't the last one in the vector)
  // to the deleted position.
  // Decrement the vector size by 1.
  // Moving the pointer to a timer within the vector doesn't invalidate the
  // pointer, so it's perfectly safe.
  // We then free the memory used by the timer.
}

// The expiry logic remains similar. We just traverse an array of pointers now
// instead of a doubly linked list.
void expire_timers(uint64_t* ids, uint64_t size) {
  // If it wasn't already clear this is pseudo code.
  deadline = calculate_deadline();
  int num_ids_added = 0;
  for (bucket : every bucket that could contain expired timers) {
    for (timer : bucket) {
      if (0 >= timer->remainingRounds && timer->deadline <= deadline) {
        append_to_ids(ids, size, &num_ids_added, timer->id);
        cancel_timer(timer);
      } else {
        --timer->remainingRounds;
      }
    }
  }
}
```
So our algorithm characteristics in brief are:

1.  To add a timer, just append it to the appropriate vector - ```O(1)```.
2.  To cancel a timer, delete it from the middle of the vector and move a pointer to occupy the hole  - ```O(1)```.
3.  To clean up all expired timers - Traverse the vector of timers and delete expired ones - ```O(expired timers)```. Again actual time depends on how many timers hashed onto a bucket.

###### Comments on implementation.

This is a slight improvement on our base line. By using a vector of pointers to timers we have removed the need for the next pointers - a slight improvement in space usage. We still have the terrible pattern of having to  use ```malloc()``` and ```free()``` on each ```add_timer()``` and ```cancel_timer()``` call. During expiry of timers we now traverse a vector of pointers to timers instead of a linked list. This is only marginally better than the first implementation since the timers themselves are allocated randomly.

#####3. Vector of inlined timers.
<p align="center">
<img src="/images/hashed-wheel-timer-inlined-vector.svg" width="500">
</p>

Let's see if we can improve effiency by making our interface even more specialized. So far we have returned a ```Timer*``` on an ```add_timer()``` call. Our intented use for the ```Timer*``` is to cancel the timer using this pointer. Thus we will end up stashing this pointer somewhere. Maybe on a per connection structure or a hash map or something. What if we could store a pointer to this timer holder structure (that points to our timer) in our timer? We could then safely move/invalidate the pointer to a timer, updating the only place where this timer was actually referenced. Here we assume that the pointer to the timer was stashed in only one place. This is somewhat like our own little garbage collector updating references to timer objects that were moved around. Let's look at our new data structures:

``` cpp NewTimer.h

// Holder of a pseudo-pointer to a timer.
// This can be used to cancel the timer.
struct TimerHolder {
  uint32_t bucket_number;
  uint32_t index_within_bucket;
};

struct Timer {
  uint64_t id;
  uint64_t deadline;
  uint64_t remaining_rounds;
  // Pointer to the sole container of this timer.
  TimerHolder* holder;
};

struct TimerBucket {
  int size;
  int capacity;
  // Array of Timers.
  Timer* timers;
};
```
Our modified interface now is:
``` cpp TimerWheel.h
// Put the pointer to the timer in the holder.
void add_timer(uint64_t delay, uint64_t id, TimerHolder* holder);

// The TimerHolder is always kept up to date. Since this is a single threaded timer
// this is not impossible to ensure.
void cancel_timer(TimerHolder* timer);

// Write the list of expired ids into the input array, assuming it is long enough.
void expire_timers(uint64_t* ids, uint64_t size);
```

Our algorithms look like
``` cpp TimerWheel.cpp
void add_timer(uint64_t delay, uint64_t id, TimerHolder* holder) {
  TimerBucket* bucket = findBucket(timer);
  // Just append timer to end of the bucket, no malloc needed.
  // Update the holder to contain the bucket_number and index_within_bucket.
  initalize_timer(bucket, delay, id, holder);
}

void cancel_timer(TimerHolder* holder) {
  // Do some sanity checking first.
  TimerBucket* bucket = find_bucket(holder->bucket_number);
  uint32_t cancelled_timer_index = holder->index_within_bucket;
  Timer* timer = find_timer(bucket, cancelled_timer_index);
  // We need to cancel this timer.
  // Just memcpy the last timer in this bucket to occupy the deleted place.
  // A timer is just 32 bytes, copying it VS copying a pointer is not a big deal.
  // If the cancelled timer is the last timer in this bucket no copy is needed.
  // Decrement the vector size by 1.
  Timer* moved_timer = move_last_timer_if_needed(bucket, cancelled_timer_index);
  if (moved_timer != nullptr) {
    // If a timer that was moved, change it's holder's offsets, 
    // so it points to the new location of the timer.
    adjust_holder_pointer(moved_timer->holder, cancelled_timer_index);
  }
  // The holder for the deleted timer should now contain a null ptr.
  // The caller will decide what to do with the holder after this function returns.
  invalidate_holder_timer(holder);
}

// The expiry logic remains similar. We just traverse an array of inlined timers now.

void expire_timers(uint64_t* ids, uint64_t size) {
  // If it wasn't already clear this is pseudo code.
  deadline = calculate_deadline();
  int num_ids_added = 0;
  for (bucket : every bucket that could contain expired timers) {
    for (timer : bucket) {
      if (0 >= timer->remainingRounds && timer->deadline <= deadline) {
        append_to_ids(ids, size, &num_ids_added, timer->id);
        cancel_timer(timer->holder);
      } else {
        --timer->remainingRounds;
      }
    }
  }
}
```
So our algorithm characteristics in brief are:

1.  To add a timer, just scribble some data to the end of the appropriate vector - ```O(1)```.
2.  To cancel a timer, copy the last timer in the bucket to the position of the deleted one and adjust references to the moved timer - ```O(1)```.
3.  To clean up all expired timers - Traverse the vector of timers and delete expired ones using the ```cancel_timer()``` call - ```O(expired timers)```. Again actual time depends on how many timers hashed onto a bucket.

###### Comments on implementation.

We no longer call ```malloc()``` and ```free()``` on every timer call. Instead we manage large buckets and copy small amounts of data around to manage deletions. We ended up storing a pointer to the holder of the timer object but overall we are not storing any more data that the other implementations. When we got rid of the ```malloc()``` and ```free()``` calls we also got rid of any fragmentation arising from them. Further during expiry processing we iterate through a chunk of contiguous memory instead of pointer chasing.

### Conclusion

By analyzing the context of our timer algorithm we were able to come up with a better implementation albeit a more tightly coupled one. Wholistic analysis of a particular piece of software often opens up such opportunities for efficiency gains. Though many a time there is a ```efficiency``` VS ```other-non-tangibles``` trade-off, I've been surprised by the number of times such gains have been made without tigher coupling.