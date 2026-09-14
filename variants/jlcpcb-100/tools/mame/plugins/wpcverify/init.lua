local exports = {name = 'wpcverify', version = '1.0', description = 'Raw WPC register recorder', license = 'BSD-3-Clause'}
function exports.startplugin()
    local taps, log, fields, actions, next_action = {}, nil, {}, {}, 1
    local stop_subscription
    local output = assert(os.getenv('WPC_TRACE_DIR'), 'WPC_TRACE_DIR required')
    local scenario = os.getenv('WPC_SCENARIO') or 'boot'
    local function event(kind, address, data, mask)
        log:write(string.format('%.12f,%s,%04x,%02x,%02x\n', manager.machine.time:as_double(), kind, address, data, mask))
    end
    emu.register_prestart(function()
        if log then event('S',0,0,0); return end
        log = assert(io.open(output .. '/bus.csv', 'w'))
        log:write('time,kind,address,data,mask\n')
        local listing = assert(io.open(output .. '/inputs.txt', 'w'))
        for tag, port in pairs(manager.machine.ioport.ports) do
            for name, field in pairs(port.fields) do
                fields[field.name] = field
                listing:write(tag .. '\t' .. field.name .. '\n')
            end
        end
        listing:close()
        local space = manager.machine.devices[':maincpu'].spaces['program']
        taps[1] = space:install_write_tap(0x3fe0, 0x3fe6, 'wpc_outputs', function(a,d,m) event('W',a,d,m) end)
        taps[2] = space:install_write_tap(0x3fff, 0x3fff, 'wpc_watchdog', function(a,d,m) event('W',a,d,m) end)
        taps[3] = space:install_read_tap(0x3fff, 0x3fff, 'wpc_zc', function(a,d,m) event('R',a,d,m) end)
        taps[4] = space:install_write_tap(0x3fd4, 0x3fd4, 'wpc_flippers', function(a,d,m) event('W',a,d,m) end)
        local f = io.open(output .. '/actions.csv', 'r')
        if f then
            for line in f:lines() do
                local t, name, value = line:match('^([%d.]+),([^,]+),([01])$')
                if t then actions[#actions+1] = {tonumber(t),name,tonumber(value)} end
            end
            f:close()
        end
        emu.print_info('WPC recorder attached at ' .. manager.machine.time:as_double() .. ' scenario=' .. scenario)
    end)
    local reset_done, snapshots = false, {}
    emu.register_frame_done(function()
        local t = manager.machine.time:as_double()
        -- MAME's driver instructions require a reset after initial factory settings.
        if t > 4 and not reset_done then reset_done = true; manager.machine:soft_reset() end
        while actions[next_action] and t >= actions[next_action][1] do
            local action = actions[next_action]
            assert(fields[action[2]], 'Unknown input: ' .. action[2]):set_value(action[3])
            event('I',next_action,action[3],255)
            next_action = next_action + 1
        end
        for _, second in ipairs({3,10,20,30,36,39,42,45,49,52,55,60,90,120,160,174,180,220,250,262,280,310}) do
            if t >= second and not snapshots[second] then
                snapshots[second] = true
                for tag, screen in pairs(manager.machine.screens) do
                    screen:snapshot(output .. '/screen-' .. second .. '-' .. tag:gsub(':','') .. '.png')
                end
                log:flush()
            end
        end
    end)
    stop_subscription = emu.add_machine_stop_notifier(function() if log then log:flush(); log:close(); log=nil end end)
end
return exports
