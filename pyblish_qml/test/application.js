function queueMe(response)
{
    console.log('!!!!Defined Function Called: ' + response + "\n");
}

function onLoad()
{
    console.log("onLoad start==================")

    ice.enqueue('#version 1', queueMe);
    ice.enqueue('#test', function test() { console.log('!!!! RAN ME TO ANONYMOUSE');});
    ice.enqueue('#asdft', function newtest(reply) { console.log('!!!! PASS DATA:    ' + reply + "\n");});
    console.log("     =========================")
    ice.processResponses();

    console.log("onLoad done==================")
}