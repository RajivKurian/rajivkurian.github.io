---
layout: post
title: "Reading length prefixed protocols"
date: 2014-11-11 19:52:23 -0800
comments: true
categories: 
---
### Why length prefixed protocols?

Protocol design can have a suprisingly large effect on performance. Text-based protocols while good for human readability are far from ideal when it comes to performance. Unless your application almost exclusively deals with strings, a binary protocol could offer significant savings. There is a lot of dogma surrounding binary protocols:
<!-- more -->
1.  **They are not extensible**: Though it is easy to corner yourself while designing your own binary protocol, this comes from a lack of experience rather than an inherent property. Look at the design of binary interchange formats like Google Protocol Buffers, FIX, Cap'n Proto etc to see how they address the issues of future extensions.
2.  **They are difficult to debug**: This really boils down to the fact that binary protocols are not human readable like XML or JSON are. Building simple tools overcomes these issues. Writing a simple ```toString()``` method on the objects that you are transferring is already a big step in being able to debug your protocol.
3.  **What about web clients?**: If your service talks to web clients, this is a valid concern. JSON is the de-facto protocol used for server web-client interactions. It's terribly easy to convert Javascript objects to and from JSON. Modern browsers now have support for binary data via [typed arrays](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Typed_arrays). These can be used to [receive and send](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Sending_and_Receiving_Binary_Data) binary data using the standard XMLHttpRequest interface. You are stuck without a solution on older browsers though so maybe this isn't a great choice at this time.


So far we have been talking about binary protocols in general. A length prefixed protocol requires every request be prefixed by its length in bytes. So the first 4/8 bytes of the request tell us the length of the actual payload. The rest of the payload could be text based instead of binary, but that's usually not the norm.

#### What can we do with a length prefixed protocol?
Length prefixed protocols allow us to cheaply check to see if an entire request has been received. All you need to check is to see if you have received all the bytes you were promised. The actual parsing and procesing of the request can be done later, maybe on another thread.

The rest of the article shows some techniques on how to read a length-prefixed request.
##### Technique 1.
<p align="center">
<img src="/images/lpp-2.svg">
</p>

The above approach lets us pick appropriately sized buffers for each request instead of guessing buffer sizes and copying later. It suffers from a problem though. Even for the smallest of requests we need at least **two read calls**. System calls are expensive and should be avoided if possible. Can we do better? We could trade the extra system calls for more complexity, a worse pathological case and larger internal framgentation.
##### Technique 2.
<p align="center">
<img src="/images/lpp-3.svg">
</p>

So if we pick a default buffer size D, such that most of our requests are of ```size D or less```, we minimize the number of read calls. When our requests are of ```size greater than D``` we incur some copy. The copy isn't that bad especially if our requests are small. Picking the default buffer size depends on the application. Erring on each side has different shortcomings:

1.  Pick too big a size: Internal fragmentation. We have too much unused space.
2.  Pick too small a size: Multiple system calls and copying. This is marginally worse than our previous approach, since it involves the extra copying.

Yet another approach is to not copy the contents of the default buffer but to use a ```list of buffers``` to hold our request. Since we know the length of our request, we are guaranteed that the list will be of size 1 or 2.
##### Technique 3.
<p align="center">
<img src="/images/lpp-4.svg">
</p>

Here we use scatter reads to read into our default buffer and the overflow buffer using the same system call. We avoid the extra copy but have our request spread over two buffers incurring random read costs when parsing the request.

The right approach depends on what trade-offs make sense for the particular application.

#### A work of caution - Slowloris attacks.

Though other protocols are vulnerable to [slowloris attacks](http://en.wikipedia.org/wiki/Slowloris), servers that use length prefixed protocols are vulnerable to a particularly nasty attack. Imagine the following attack:

``` cpp Slowloris attack
1. Client connects and says it has a giant request, say of 64 MB.
2. Server allocates a buffer of size 64 MB waiting for the bytes.
3. Client never sends additional bytes or sends a trickle of bytes infrequently.
```
Not only did the client tie up a connection, it also tied up memory. A flood of these attacks could cause the server to exhaust all buffers. The standard techniques to mitigate slowloris attacks still apply:

1.  Timers to disconnect idle clients. Some attackers will send a byte or two every now and then to defeat timers. We could mark a client as ```potentially evil``` if it only sends a trickle of bytes one too many times. We could also make our timer more strict for clients we suspect.
2.  Limit the number of connections/requests from the same IP address.
3.  Maintain a blacklist that keeps evolving. Deny connection requests from IP addresses on the blacklist.

We can modify our default buffer size technique to make it more resistant to buffer exhaustion:

1.  Maintain a default buffer size per client. Start with a low buffer size and as the client gains more trust, increase it up to a limit.
2.  Instead of allocating a buffer of the appropriate size as soon as we know the request length, we could let the client fill up the default buffer before we allocate an overflow buffer. This way we only tie up a smaller buffer till we absolutely need overflow space.

The simplest defense though is to use these protocols on trusted networks instead of on the open web.

#### Conclusion
Length prefixed protocols make it really easy to check if a particular request is ready for parsing or not. This is especially a boon for multi-threaded servers where one thread could read bytes off the network and pass a complete request to another thread for parsing and processing. The cheap check implies that the network-thread doesn't have to do much work to decide when to transfer a request to the next stage in the pipeline. The request might still be ill-formed but the parsing/processing thread could take care of it. Let me know in the comments section, if you use other techniques to read length prefixed protocols or if I have missed something.