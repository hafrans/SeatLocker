

"""
    获取开启抢座的而且有使用点数的
"""
SQL_ALL_AUTOCHECKIN_PERSON = """
                select
                    u.id as id,
                    u.username as username,
                    u.password as password,
                    u.token as token,
                    u.register_time as register_time,
                    u.priority as priority,
                    u.school as school,
                    s.email as email,
                    s.phone as phone ,
                    s.checkin as checkin,
                    s.reserve as reserve,
                    s.auto_checkin as auto_checkin,
                    s.random_reserve as random_reserve
                from users as u inner join settings as s on s.user = u.id where s.auto_checkin > 0 and s.checkin > -2 and s.checkin != 0
                """

"""
    获取时间段内
     (
        julianday(datetime('now','localtime')) >= julianday(start_date) and julianday(datetime('now','localtime')) <= julianday(end_date) 
        or julianday(datetime('now','localtime')) >= julianday(start_date) and end_date is null
        ) 
    并且剩余reserve点数大于-1，而且开启自动抢座
"""
SQL_ALL_RESERVATION_PERSON = """
    select 
          users.id as id,
          seat.user as user ,
          users.username as username,
          users.password as password,
          users.school as school,
          settings.reserve as reserve
    from 
          seat 
    inner join
          settings
    on
          seat.user = settings.user
    inner join
          users
    on    seat.user = users.id and settings.user = users.id
    where  (
        julianday(datetime('now','localtime')) >= julianday(start_date) and julianday(datetime('now','localtime')) <= julianday(end_date) 
        or julianday(datetime('now','localtime')) >= julianday(start_date) and end_date is null
        ) 
          and settings.reserve != -2 and settings.auto_reserve = 1 
    group by seat.user
"""
"""
    获取某个人的座位信息
"""
SQL_ALL_RESERVATION_SEATS = """
                select
                    s.email as email,
                    s.phone as phone ,
                    s.reserve as reserve,
                    s.random_reserve as random_reserve,
                    s.auto_reserve as auto_reserve,
                    e.user as user,
                    e.room as room,
                    e.seat as seat,
                    e.name as name,
                    e.start_time as start_time,
                    e.end_time as end_time,
                    e.start_date as start_date,
                    e.end_date as end_date,
                    e.priority as priority,
                    e.tuesday as tuesday
                from settings as s inner join seat as e on s.user = e.user
                where (
                    julianday(datetime('now','localtime')) >= julianday(start_date) and julianday(datetime('now','localtime')) <= julianday(end_date) 
                    or julianday(datetime('now','localtime')) >= julianday(start_date) and end_date is null
                    ) 
                    and s.reserve != -2 and s.auto_reserve = 1 and e.user = ? order by e.priority desc, e.id asc

"""