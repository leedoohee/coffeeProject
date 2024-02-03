-- 초기 데이터
insert into coffeeadmin_category(p_category_id, category_id, category_name) value ('', '001', 'beverage');
insert into coffeeadmin_category(p_category_id, category_id, category_name) value ('', '002', 'cup');
insert into coffeeadmin_category(p_category_id, category_id, category_name) value ('', '003', 'tumbler');

insert into coffeeadmin_size(size_id, category_id, size_name) value (1, '001', 'regular');
insert into coffeeadmin_size(size_id, category_id, size_name) value (2, '001', 'grande');
insert into coffeeadmin_size(size_id, category_id, size_name) value (3, '001', 'venti');
insert into coffeeadmin_size(size_id, category_id, size_name) value (4, '002', 'S');
insert into coffeeadmin_size(size_id, category_id, size_name) value (5, '002', 'L');
insert into coffeeadmin_size(size_id, category_id, size_name) value (6, '003', 'S');
insert into coffeeadmin_size(size_id, category_id, size_name) value (7, '003', 'L');

insert into coffeeadmin_color(color_id, category_id, color_name) value (1, '002', 'red');
insert into coffeeadmin_color(color_id, category_id, color_name) value (2, '002', 'green');

insert into coffeeadmin_color(color_id, category_id, color_name) value (3, '002', 'red');
insert into coffeeadmin_color(color_id, category_id, color_name) value (4, '002', 'green');

-- 검색 테이블
CREATE TABLE product_search
(
    product_id           VARCHAR(50)  primary key NOT NULL,
    product_name         VARCHAR(100) NOT NULL,
    product_code         VARCHAR(128) NOT NULL,
    description  		 longtext NOT NULL,
    size_list            VARCHAR(50)  NOT NULL,
    color_list            VARCHAR(50)  NOT NULL,
    price				 int(11)   not null
);


-- 트리거 생성
DELIMITER $$
    DROP TRIGGER IF EXISTS product_trigger$$
	CREATE TRIGGER product_trigger
	AFTER INSERT ON coffeeadmin_productoption
	FOR EACH ROW
	BEGIN
        DECLARE done INT DEFAULT FALSE;
		DECLARE product_id VARCHAR(50);
		DECLARE product_name VARCHAR(100);
		DECLARE product_code VARCHAR(128);
		DECLARE description longtext;
		DECLARE size_list VARCHAR(50);
        DECLARE color_list VARCHAR(50);
        DECLARE price int(11);
        DECLARE cur CURSOR FOR (select
			cp.product_name, cp.product_code, cp.description, list.size_list, list.color_list, cp2.price
		from
			coffeeadmin_product cp
            inner join coffeeadmin_price cp2 on cp.product_id = cp2.product_id
            left outer join (
				select
				   cp.product_id,
				   group_concat(distinct substring_index(option_name,'^',1)) as color_list,
				   group_concat(distinct substring_index(option_name,'^',-1)) as size_list
			   from
				   coffeeadmin_product cp
				   left outer join coffeeadmin_productoption cpp on cp.product_id = cpp.product_id
			   where
					cp.product_id = NEW.product_id
				   group by
					   cp.product_id
		   ) list on list.product_id = cp.product_id
		where cp.product_id = NEW.product_id);
		DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

        OPEN cur;
			ins_loop: LOOP
				FETCH cur INTO product_name, product_code, description, size_list, color_list, price;
				IF done THEN
					LEAVE ins_loop;
				END IF;
				INSERT INTO product_search VALUE (NEW.product_id,  product_name,  product_code,  description,  size_list,  color_list,  price);
			END LOOP;
		CLOSE cur;
	END $$
DELIMITER ;
