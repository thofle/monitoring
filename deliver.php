<?php

require 'vendor/autoload.php'; 

class deliver
{
    private $payload;
    private $signature;
    private $host_id;
    private $mongo;

    function __construct($payload, $signature, $host_id)
    {
        $this->payload = $payload;
        $this->host_id = $host_id;
        $this->signature = $signature;
        $this->mongo = $this->getMongoDBObject();
    }

    function __destruct()
    {
        unset($this->mongo);
    }

    function getMongoDBObject()
    {
        $mongoURI = 'mongodb://' . MONGODB_USER . ':' . MONGODB_PASS . "@" . MONGODB_HOST . '/' . MONGODB_DATABASE;
        return new MongoDB\Client($mongoURI);
    }

    function getHostConfig()
    {
        $collection = $this->mongo->monitoring->config;
        $result = $collection->find([ 'host_id' => $this->host_id ]);
        
    }

    function getPublicKey()
    {
        // gets public key for host_id
        // 
        $publicKey = "key"
        return $publicKey;
    }

    function verifySignature()
    {
        $publicKey = $this->getPublicKey();
        $result = openssl_verify($this->payload, $this->signature, $publicKey);
        openssl_free_key($publicKey);

        if ($result == 1)
            return true;
        elseif ($result == 0)
            return false;
        else
            throw new Exception("Unable to verify signature");
    }

    function save()
    {
        if ($this->verifySignature !== true)
            throw new Exception("Invalid signature");

        $this->savePayloadToDB()
    }

    function savePayloadToDB()
    {
        // saves payload to db
    }
}