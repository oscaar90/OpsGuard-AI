<?php
return [
    'debug' => true, // BAD PRACTICE: Debug en true
    'database' => [
        'host' => 'localhost',
        // IA debe detectar password hardcodeada, aunque sea genérica
        'password' => 'admin1234', 
    ],
    'openai' => [
        // IA debe detectar que esto debería ser una variable de entorno
        'api_key' => 'sk-proj-1234567890abcdef1234567890abcdef', 
    ]
];